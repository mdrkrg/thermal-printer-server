// State
const items = []
let imageBase64 = null
let currentType = 'text'

// Theme

const THEMES = {
  terminal: {
    href: 'https://unpkg.com/terminal.css@0.7.5/dist/terminal.min.css',
    bodyClass: 'terminal',
    windowed: false,
  },
  xp: {
    href: 'https://unpkg.com/xp.css@0.2.6/dist/xp.css',
    bodyClass: 'theme-windowed',
    windowed: true,
  },
  98: {
    href: 'https://unpkg.com/xp.css@0.2.6/dist/98.css',
    bodyClass: 'theme-windowed theme-98',
    windowed: true,
  },
}

function setTheme(name) {
  const theme = THEMES[name]
  if (!theme) return

  // Swap stylesheet
  document.getElementById('theme-link').href = theme.href

  // Reset body classes, apply new ones
  document.body.className = theme.bodyClass

  // Show/hide XP window chrome
  const win = document.getElementById('xp-window')
  const content = document.getElementById('main-content')
  const title = document.getElementById('main-title')
  if (theme.windowed) {
    win.classList.remove('hidden')
    title.classList.add('hidden')
    // Move main content into window body if not already there
    const body = document.getElementById('xp-body')
    if (!body.contains(content)) body.appendChild(content)
  } else {
    win.classList.add('hidden')
    title.classList.remove('hidden')
    // Move main content back to document body if it was inside the window
    if (!document.body.contains(content) || document.getElementById('xp-body').contains(content)) {
      document.body.appendChild(content)
    }
  }

  // Mark active button
  document.querySelectorAll('#theme-switcher button').forEach((btn) => {
    if (btn.dataset.theme === name) {
      btn.dataset.active = ''
    } else {
      delete btn.dataset.active
    }
  })

  localStorage.setItem('theme', name)
}

// Status

function updateStatus(event) {
  try {
    const data = JSON.parse(event.detail.xhr.responseText)
    const indicator = document.getElementById('status-indicator')
    const text = document.getElementById('status-text')
    const paper = document.getElementById('status-paper')
    indicator.className = data.online ? 'online' : 'offline'
    text.textContent = data.online ? 'Online' : 'Offline'
    paper.textContent = `Paper: ${data.paperStatus ?? '—'}`
  }
  catch (_) { }
}

// Init

document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('theme') || 'terminal'
  setTheme(saved)
  htmx.trigger(document.getElementById('refresh-btn'), 'click')
  updatePreview()
})

// Type switching

function switchType(type) {
  currentType = type;
  ['text', 'qr', 'barcode', 'image', 'cut'].forEach((t) => {
    document.getElementById(`form-${t}`).classList.toggle('hidden', t !== type)
  })
  document.querySelectorAll('#type-tabs button').forEach((btn, i) => {
    const types = ['text', 'qr', 'barcode', 'image', 'cut']
    btn.classList.toggle('active', types[i] === type)
    btn.classList.toggle('btn-ghost', types[i] === type)
  })
}

// Image handling

function previewImage(input) {
  const file = input.files[0]
  if (!file) {
    imageBase64 = null
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    imageBase64 = e.target.result
    const wrap = document.getElementById('image-preview-wrap')
    const img = document.getElementById('image-preview')
    img.src = imageBase64
    wrap.classList.remove('hidden')
  }
  reader.readAsDataURL(file)
}

// Add item

function addItem(type) {
  const item = { type }
  if (type === 'text') {
    const content = document.getElementById('text-content').value
    if (!content) { alert('Content is required'); return }
    item.content = content
  }
  else if (type === 'qr') {
    const content = document.getElementById('qr-content').value
    if (!content) { alert('Content is required'); return }
    item.content = content
    item.size = Number.parseInt(document.getElementById('qr-size').value, 10)
    item.center = document.getElementById('qr-center').value === 'true'
  }
  else if (type === 'barcode') {
    const content = document.getElementById('barcode-content').value
    if (!content) { alert('Content is required'); return }
    item.content = content
    item.format = document.getElementById('barcode-format').value
    item.height = Number.parseInt(document.getElementById('barcode-height').value, 10)
    item.width = Number.parseInt(document.getElementById('barcode-width').value, 10)
    item.textPosition = document.getElementById('barcode-text-position').value
  }
  else if (type === 'image') {
    if (!imageBase64) { alert('Please select an image file'); return }
    item.source = imageBase64
    item.impl = document.getElementById('image-impl').value
    item.fragmentHeight = Number.parseInt(document.getElementById('image-fragment-height').value, 10)
    item.center = document.getElementById('image-center').value === 'true'
    item.highDensityVertical = document.getElementById('image-hd-v').value === 'true'
    item.highDensityHorizontal = document.getElementById('image-hd-h').value === 'true'
  }
  else if (type === 'cut') {
    item.enabled = document.getElementById('cut-enabled').value === 'true'
  }
  items.push(item)
  renderItems()
  updatePreview()
}

// Render item list

function renderItems() {
  const list = document.getElementById('items-list')
  list.innerHTML = ''
  items.forEach((item, i) => {
    const li = document.createElement('li')
    let summary = ''
    if (item.type === 'text') summary = JSON.stringify(item.content).slice(0, 60)
    else if (item.type === 'qr') summary = item.content
    else if (item.type === 'barcode') summary = `${item.content} (${item.format})`
    else if (item.type === 'image') summary = '[image data]'
    else if (item.type === 'cut') summary = `enabled: ${item.enabled}`
    li.innerHTML = `
      <div class="item-header">
        <span class="item-type">${item.type}</span>
        <div style="display:flex;gap:0.25rem;">
          <button onclick="moveItem(${i}, -1)" ${i === 0 ? 'disabled' : ''}>↑</button>
          <button onclick="moveItem(${i}, 1)" ${i === items.length - 1 ? 'disabled' : ''}>↓</button>
          <button class="danger" onclick="removeItem(${i})">✕</button>
        </div>
      </div>
      <div class="item-summary">${summary}</div>
      <div class="item-preview" id="preview-${i}"></div>`
    list.appendChild(li)
    renderPreview(item, i)
  })
}

function renderPreview(item, index) {
  const previewEl = document.getElementById(`preview-${index}`)
  if (!previewEl) return

  if (item.type === 'text') {
    previewEl.innerHTML = `<div class="preview-text">${escapeHtml(item.content)}</div>`
  }
  else if (item.type === 'qr') {
    previewEl.innerHTML = `<div class="preview-qr">
      <div class="qr-placeholder" style="width:${item.size * 20}px;height:${item.size * 20}px;${item.center ? 'margin:0 auto;' : ''}">
        QR Code<br>${item.size}x
      </div>
    </div>`
  }
  else if (item.type === 'barcode') {
    const textPos = item.textPosition
    previewEl.innerHTML = `<div class="preview-barcode">
      ${(textPos === 'ABOVE' || textPos === 'BOTH')
        ? `<div class="barcode-text">${escapeHtml(item.content)}</div>`
        : ''}
      <div class="barcode-placeholder" style="height:${item.height}px;">
        ${item.format}
      </div>
      ${(textPos === 'BELOW' || textPos === 'BOTH')
        ? `<div class="barcode-text">${escapeHtml(item.content)}</div>`
        : ''}
    </div>`
  }
  else if (item.type === 'image') {
    previewEl.innerHTML = `<div class="preview-image">
      <img src="${item.source}" style="max-width:100%;height:auto;${item.center ? 'margin:0 auto;' : ''}">
    </div>`
  }
  else if (item.type === 'cut') {
    previewEl.innerHTML = `<div class="preview-cut">
      ${item.enabled ? '✂ -------------------' : '(cut disabled)'}
    </div>`
  }
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function removeItem(i) {
  items.splice(i, 1)
  renderItems()
  updatePreview()
}

function moveItem(i, dir) {
  const j = i + dir
  if (j < 0 || j >= items.length) return;
  [items[i], items[j]] = [items[j], items[i]]
  renderItems()
  updatePreview()
}

function clearItems() {
  items.length = 0
  renderItems()
  updatePreview()
  document.getElementById('response-box').textContent = ''
}

// JSON Preview

function updatePreview() {
  const display = items.map((item) => {
    if (item.type === 'image') {
      return { ...item, source: `${item.source.slice(0, 40)}…[truncated]` }
    }
    return item
  })
  document.getElementById('preview').textContent
    = JSON.stringify({ items: display }, null, 2)
}

// Submit

async function submitJob() {
  if (items.length === 0) { alert('Add at least one item'); return }
  const statusEl = document.getElementById('submit-status')
  const responseBox = document.getElementById('response-box')
  statusEl.textContent = 'Sending…'
  responseBox.textContent = ''
  responseBox.className = ''
  try {
    const res = await fetch('/print', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items }),
    })
    const data = await res.json()
    responseBox.textContent = JSON.stringify(data, null, 2)
    responseBox.className = res.ok ? '' : 'error'
    statusEl.textContent = res.ok ? 'Done' : 'Error'
  }
  catch (err) {
    responseBox.textContent = String(err)
    responseBox.className = 'error'
    statusEl.textContent = 'Error'
  }
}
