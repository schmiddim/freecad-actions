# Open Tasks / Agents

This file tracks tasks that require manual action or future follow-up.

## Pending

### Pin schema URLs to a release tag

**Context:** `cad-gallery.yaml` and `maker.yaml` reference schemas via
`refs/heads/master` (always latest). These should be pinned to a specific
release tag for stability.

**Action:**
1. Create a new release tag (e.g. `v1.3.0`) after the current changes are merged
2. Update the schema comments in both files:

```yaml
# cad-gallery.yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/schmiddim/freecad-actions/refs/tags/v1.3.0/schemas/cad-gallery.schema.json

# maker.yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/schmiddim/freecad-actions/refs/tags/v1.3.0/schemas/maker.schema.json
```

3. Repeat this step whenever schemas change and a new release is cut.

**Files to update:** `cad-gallery.yaml` (line 1), `maker.yaml` (line 1)
