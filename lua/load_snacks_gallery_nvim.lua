local ok, snacks = pcall(require, "snacks")

if not ok then
  vim.api.nvim_echo({ { "[Molten] `snacks.nvim` not found" } }, true, { err = true })
  return
end

local gallery_api = {}
local images = {}
local next_order = 0
local is_wezterm = vim.env.TERM_PROGRAM == "WezTerm"
local gallery_position = "bottom"

local function restore_cursor()
  if not is_wezterm or vim.api.nvim__redraw == nil then
    return
  end

  vim.schedule(function()
    pcall(vim.api.nvim__redraw, { cursor = true, flush = true })
  end)
end

local function close_image(img)
  if not img then
    return
  end

  if img.buf and vim.api.nvim_buf_is_valid(img.buf) then
    pcall(snacks.image.placement.clean, img.buf)
  end

  if img.placement then
    pcall(function()
      img.placement:close()
    end)
    img.placement = nil
  end

  if img.win and vim.api.nvim_win_is_valid(img.win) then
    pcall(vim.api.nvim_win_close, img.win, true)
  end
  img.win = nil

  if img.buf and vim.api.nvim_buf_is_valid(img.buf) then
    pcall(vim.api.nvim_buf_delete, img.buf, { force = true })
  end
  img.buf = nil
end

local function get_host_win(img)
  if img.host_win and img.host_win ~= vim.NIL and vim.api.nvim_win_is_valid(img.host_win) then
    return img.host_win
  end

  local bufinfo = vim.fn.getbufinfo(img.host_buf)
  if #bufinfo == 0 or not bufinfo[1].windows or #bufinfo[1].windows == 0 then
    return nil
  end
  return bufinfo[1].windows[1]
end

local function fit_size(img)
  return snacks.image.util.fit(img.path, {
    width = snacks.config.image.doc and snacks.config.image.doc.max_width or 80,
    height = snacks.config.image.doc and snacks.config.image.doc.max_height or 40,
  })
end

local function ensure_window(img, host_win, row, col, width, height, relative_mode)
  if img.buf == nil or not vim.api.nvim_buf_is_valid(img.buf) then
    img.buf = vim.api.nvim_create_buf(false, true)
    vim.bo[img.buf].bufhidden = "wipe"
    vim.bo[img.buf].swapfile = false
    vim.bo[img.buf].modifiable = false
    vim.bo[img.buf].filetype = "image"
  end
  vim.b[img.buf].molten_image_path = img.path

  local win_opts = {
    relative = relative_mode,
    row = row,
    col = col,
    width = width,
    height = height,
    style = "minimal",
    border = "none",
    focusable = false,
    zindex = 60,
  }

  if relative_mode == "win" then
    win_opts.win = host_win
  end

  if img.win and vim.api.nvim_win_is_valid(img.win) then
    vim.api.nvim_win_set_config(img.win, win_opts)
  else
    win_opts.noautocmd = true
    img.win = vim.api.nvim_open_win(img.buf, false, win_opts)
  end

  if img.placement == nil or img.placement.closed then
    img.placement = snacks.image.placement.new(img.buf, img.path, {
      inline = false,
      auto_resize = false,
      on_update = restore_cursor,
      width = width,
      height = height,
    })
  end
end

local function layout_host(host_buf)
  local host_images = {}
  for _, img in pairs(images) do
    if img.visible and img.host_buf == host_buf then
      table.insert(host_images, img)
    end
  end

  if #host_images == 0 then
    return
  end

  table.sort(host_images, function(a, b)
    return a.order < b.order
  end)

  local host_win = get_host_win(host_images[1])
  if not host_win then
    for _, img in ipairs(host_images) do
      close_image(img)
    end
    return
  end

  local editor_width = vim.o.columns
  local editor_height = vim.o.lines
  local gap = 2
  local host_width = vim.api.nvim_win_get_width(host_win)
  local host_height = vim.api.nvim_win_get_height(host_win)
  local host_info = vim.fn.getwininfo(host_win)[1]

  local current_row
  local current_col
  local width_limit
  local height_limit
  local relative_mode

  if gallery_position == "right" then
    current_row = math.max(host_info.winrow - 1, 0)
    current_col = host_images[1].anchor_col and (host_images[1].anchor_col + gap) or nil
    if current_col == nil or current_col >= editor_width - 20 then
      width_limit = math.max(40, math.floor(editor_width * 0.5))
    else
      width_limit = math.max(20, editor_width - current_col - gap)
    end
    height_limit = math.max(1, editor_height - current_row - 2)
    relative_mode = "editor"
  else
    current_row = host_height + gap
    current_col = 0
    width_limit = host_width
    height_limit = math.max(1, editor_height - current_row - 2)
    relative_mode = "win"
  end

  for _, img in ipairs(host_images) do
    local size = fit_size(img)
    local width = math.max(1, math.min(size.width, width_limit))
    local height = math.max(1, math.min(size.height, height_limit))

    if width < 1 or height < 1 then
      close_image(img)
    else
      if gallery_position == "right" then
        if img.anchor_col and img.anchor_col < editor_width - 20 then
          current_col = math.min(
            math.max(img.anchor_col + gap, 0),
            math.max(editor_width - width - gap, 0)
          )
        else
          current_col = math.max(editor_width - width - gap, 0)
        end
      end
      ensure_window(img, host_win, current_row, current_col, width, height, relative_mode)
      current_row = current_row + height + gap
    end
  end
end

gallery_api.configure = function(position)
  if position == "right" or position == "bottom" then
    gallery_position = position
  else
    gallery_position = "bottom"
  end
end

gallery_api.from_file = function(path, opts)
  local identifier = opts.id or path
  if images[identifier] then
    local img = images[identifier]
    img.path = path
    img.host_buf = opts.buffer
    img.host_win = opts.window
    img.anchor_col = vim.b[opts.buffer].molten_gallery_anchor_col
    return identifier
  end
  next_order = next_order + 1
  images[identifier] = {
    id = identifier,
    path = path,
    host_buf = opts.buffer,
    host_win = opts.window,
    anchor_col = vim.b[opts.buffer].molten_gallery_anchor_col,
    order = next_order,
    visible = false,
    buf = nil,
    win = nil,
    placement = nil,
  }
  return identifier
end

gallery_api.render = function(identifier)
  local img = images[identifier]
  if not img then
    return
  end

  img.visible = true
  layout_host(img.host_buf)
end

gallery_api.clear = function(identifier)
  local img = images[identifier]
  if not img then
    return
  end

  img.visible = false
  close_image(img)
end

gallery_api.clear_all = function()
  for _, img in pairs(images) do
    gallery_api.clear(img.id)
  end
end

gallery_api.image_size = function(_identifier)
  return { height = 0, width = 0 }
end

return { gallery_api = gallery_api }
