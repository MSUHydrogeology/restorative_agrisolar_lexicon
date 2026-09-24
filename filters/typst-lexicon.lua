-- Typst-only adjustments for the PDF. The HTML site never runs this filter:
-- everything here is something the website already does through CSS, or
-- something a single PDF needs that a multi-page site does not.
if not FORMAT:match("typst") then return {} end

local project = (quarto and quarto.project and quarto.project.directory) or "."

-- 1. Empty anchor spans, []{#id}. Typst cannot attach a label to empty
-- content, so a link to one fails to compile. Give each an invisible element.
local function anchor(id)
  return pandoc.RawInline("typst", "#metadata(none)<" .. id .. ">")
end

function Span(el)
  if el.identifier ~= "" and #el.content == 0 then return anchor(el.identifier) end
end

-- 2. Links to a whole chapter, like [Sources](sources.qmd), point at a file,
-- which is dead inside one PDF. Point them at the chapter's opening heading.
local heading_ids = {}

local function slug(s)
  return (s:lower():gsub("[^%w%s%-_%.]", ""):gsub("%s+", "-"))
end

local function chapter_id(path)
  if heading_ids[path] ~= nil then return heading_ids[path] or nil end
  local rel = path:gsub("^%.%./", "")
  for _, candidate in ipairs({ rel, "chapters/" .. rel }) do
    local f = io.open(project .. "/" .. candidate, "r")
    if f then
      for line in f:lines() do
        local title = line:match("^#%s+(.+)$")
        if title then
          f:close()
          local id = title:match("{#([^%s}]+)")
          if not id then id = slug(title:gsub("%s*{.-}%s*$", "")) end
          heading_ids[path] = id
          return id
        end
      end
      f:close()
    end
  end
  heading_ids[path] = false
  return nil
end

function Link(el)
  local path, frag = el.target:match("^([^#:]+%.qmd)(.*)$")
  if path and frag == "" then
    local id = chapter_id(path)
    if id then el.target = "#" .. id end
    return el
  end
end

-- 3. Styled boxes and banded tables. Quarto hands Typst a bare block and
-- drops the class, so tag each one with the kind the site styles it as.
local BOXES = { ["how-to"] = true, example = true, caution = true,
                welcome = true, ["draft-note"] = true, evidence = true }
local TABLES = { ["zone-table"] = true, ["position-table"] = true,
                 ["function-table"] = true, ["lever-table"] = true,
                 ["region-table"] = true, ["pressure-table"] = true,
                 ["key-column"] = true }

-- Column widths by content. Quarto gives every column an equal share, which
-- starved the long last column of the regional table while short ones sat
-- half empty. Weight each column by how much its cells say, and for a styled
-- table size the leading label column to its longest label, as the site does.
local function cell_len(cell)
  return utf8.len(pandoc.utils.stringify(cell.contents)) or 0
end

local function size_columns(tbl, label_first)
  local n = #tbl.colspecs
  if n < 2 then return nil end
  local sums, counts, longest = {}, {}, {}
  for j = 1, n do sums[j], counts[j], longest[j] = 0, 0, 0 end
  for _, body in ipairs(tbl.bodies) do
    for _, row in ipairs(body.body) do
      for j, cell in ipairs(row.cells) do
        if j <= n then
          local len = cell_len(cell)
          sums[j], counts[j] = sums[j] + len, counts[j] + 1
          if len > longest[j] then longest[j] = len end
        end
      end
    end
  end
  local weights, total, first = {}, 0, 0
  for j = 1, n do
    local mean = counts[j] > 0 and sums[j] / counts[j] or 0
    weights[j] = math.max(8, math.min(mean, 70)) ^ 0.75
  end
  if label_first then
    first = math.max(0.08, math.min(0.26, (longest[1] * 5.4 + 14) / 460))
  end
  for j = (label_first and 2 or 1), n do total = total + weights[j] end
  for j, spec in ipairs(tbl.colspecs) do
    local w
    if label_first and j == 1 then w = first
    else w = (1 - first) * weights[j] / total end
    tbl.colspecs[j] = { spec[1], w }
  end
  return tbl
end

function Table(tbl) return size_columns(tbl, false) end

local function wrap(call, el)
  local out = { pandoc.RawBlock("typst", call .. "[") }
  if el.identifier ~= "" then
    out[1] = pandoc.RawBlock("typst", "#metadata(none)<" .. el.identifier .. ">\n" .. call .. "[")
  end
  for _, b in ipairs(el.content) do out[#out + 1] = b end
  out[#out + 1] = pandoc.RawBlock("typst", "]")
  return out
end

function Div(el)
  for _, c in ipairs(el.classes) do
    if BOXES[c] then
      return wrap('#lexicon-box("' .. c .. '")', el)
    elseif TABLES[c] then
      el = el:walk({ Table = function(tb) return size_columns(tb, true) end })
      return wrap('#lexicon-table("' .. c .. '")', el)
    end
  end
end

-- 4. The alphabetical index's letter headings (A, B, C...) would fill a page
-- of the contents. Keep them in the body and out of the outline.
function Header(el)
  if el.level == 2 and pandoc.utils.stringify(el.content):match("^%u$") then
    el.classes:insert("unlisted")
    return el
  end
end
