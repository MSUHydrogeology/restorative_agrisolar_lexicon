-- Typst only, and run before Quarto's own filters (`at: pre-ast` in
-- _quarto.yml): the website shows some figures as tabs, which a PDF cannot.
-- Lay the panels out one after another and drop the tab titles, since each
-- figure's caption already names what it shows.
if not FORMAT:match("typst") then return {} end

function Div(el)
  if el.classes:includes("panel-tabset") then
    local blocks = {}
    for _, b in ipairs(el.content) do
      if b.t ~= "Header" then blocks[#blocks + 1] = b end
    end
    return blocks
  end
end
