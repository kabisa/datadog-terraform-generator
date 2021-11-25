module "MODULE_NAME" {
  source                     = "MODULE_PATH"
  env                        = var.env
  filter_str                 = "FILTER_STR"
  service_check_include_tags = []
  additional_tags            = []
  service                    = "SERVICE"
}