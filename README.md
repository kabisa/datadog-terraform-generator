
# Terraform code generator for Datadog

## Usage

```bash
ddtfgen 
├─ -h                     # prints out help
├── init                  # initialize configuration
├── monitor_from_template # generate monitor based on generic monitor template
├── monitor_from_id       # generate monitor based on generic monitor template, but starts with existing monitor ID as input

```

## Developing

Pre-commit:
   - Install [pre-commit](http://pre-commit.com/). E.g. `brew install pre-commit`.
   - Run `pre-commit install` in the repo.
   - That’s it! Now every time you commit a code change (`.tf` file), the hooks in the `hooks:` config `.pre-commit-config.yaml` will execute.

Pip install in edit mode:

```bash
pip install -e .
```

