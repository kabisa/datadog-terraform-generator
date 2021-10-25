locals {
  MODULE_NAME_filter = coalesce(
    var.MODULE_NAME_filter_override,
    var.filter_str
  )
}

module "MODULE_NAME" {
  source = "git@github.com:kabisa/terraform-datadog-generic-monitor.git?ref=GENERIC_MONITOR_VERSION"

  name  = "MONITOR_NAME"
  query = "QUERY"

  # alert specific configuration
  require_full_window = false
  alert_message       = "ALERT_MESSAGE"
  recovery_message    = "RECOVERY_MESSAGE"

  # monitor level vars
  enabled            = var.MODULE_NAME_enabled
  alerting_enabled   = var.MODULE_NAME_alerting_enabled
  warning_threshold  = var.MODULE_NAME_warning
  critical_threshold = var.MODULE_NAME_critical
  priority           = var.MODULE_NAME_priority
  docs               = var.MODULE_NAME_docs
  note               = var.MODULE_NAME_note

  # module level vars
  env                  = var.env
  service              = var.service
  notification_channel = var.notification_channel
  additional_tags      = var.additional_tags
  locked               = var.locked
  name_prefix          = var.name_prefix
  name_suffix          = var.name_suffix
}
