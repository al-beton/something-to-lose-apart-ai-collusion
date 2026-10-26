-- Implements: reports/paper-source
-- Pull the paper's text into its skeleton: each ```{.include} block in
-- paper.md is replaced by the Markdown files it names (one per line, beside
-- paper.md), and their front matter (the abstract) joins the paper's.

function Pandoc(doc)
  local dir = pandoc.path.directory(PANDOC_STATE.input_files[1])
  local blocks = pandoc.List()
  for _, block in ipairs(doc.blocks) do
    if block.t == "CodeBlock" and block.classes:includes("include") then
      for name in block.text:gmatch("[^\n]+") do
        local file = assert(io.open(pandoc.path.join({ dir, name })), "paper: can't open " .. name)
        local part = pandoc.read(file:read("a"), "markdown", PANDOC_READER_OPTIONS)
        file:close()
        blocks:extend(part.blocks)
        for key, value in pairs(part.meta) do
          if doc.meta[key] == nil then
            doc.meta[key] = value
          end
        end
      end
    else
      blocks:insert(block)
    end
  end
  doc.blocks = blocks
  return doc
end
