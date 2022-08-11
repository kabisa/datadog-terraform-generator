
# Terraform code generator for Datadog

## Usage

First make sure auto-completions work. That and the `-h` option are the main documentation features.

Here's a list of good examples:

Generate a TF monitor. (will not terraform apply/init)
```bash
# this wil create a config file you can edit:
ddtfgen defaults_file .

# <edit the config file> 

# this will generate a monitor based on the config file:
ddtfgen monitor_from_template modules/mymodule my_monitor
```

Generate a TF monitor from existing monitor in the Datadog UI. (will not terraform import yet)
```bash
monitor_from_id 2001855 modules/mymodule
```

Generate an empty module. (You will need to use/import the module by yourself)
```bash
ddtfgen module modules/mymodule
```

Generate a TF module based on existing monitors. You can use the query just as in the Datadog UI. It will also try to guess the service_name.
This feature lets you import a whole set of monitors at once.
```bash
ddtfgen module --from_query "service:vault" modules/mymodule
```

Mass move terraform state.
Do you also like running 20 terraform state mv commands by hand?
```bash
ddtfgen mass_state_move module.a.b. module.c.d.
```

Get Host list:
```bash
ddtfgen --config_name X get_host_list --host_name_pattern "*.local" --tags_pattern "service:abc"
```

Generate services file:
This will output a yaml file that shows the dependencies between services
```bash
ddtfgen services_file prd
```

Get a summary of changes that Terraform wishes to perform
```bash
ddtfgen get_terraform_changes
```

Get monitor list from query:
```bash
ddtfgen monitors --query 'service:"kubernetes" notification:servicenow-toyotaeurope'
```

Generate a csv table:
```bash
ddtfgen table --agg_metric_names max:rabbitmq.queue.messages max:rabbitmq.queue.consumers --group_by rabbitmq_queue rabbitmq_vhost --from 1 hours ago --to now
```

Generate the TF code for log metrics

## Autocompletions

```bash
activate-global-python-argcomplete
```

add this to your `.bashrc` or `.zshrc` 

```bash
eval "$(register-python-argcomplete ddtfgen)"
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

