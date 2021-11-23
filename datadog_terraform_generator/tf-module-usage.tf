module "MODULE_NAME" {
  source                     = "MODULE_PATH"
  env                        = var.env
  filter_str                 = ""
  service_check_include_tags = []
  additional_tags            = []
  # service                  = ""
}