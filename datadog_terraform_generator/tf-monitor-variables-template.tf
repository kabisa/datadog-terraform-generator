variable "MODULE_NAME_enabled" {
  type    = bool
  default = true
}

variable "MODULE_NAME_warning" {
  type    = number
  default = WARNING
}

variable "MODULE_NAME_critical" {
  type    = number
  default = CRITICAL
}

variable "MODULE_NAME_evaluation_period" {
  type    = string
  default = "EVALUATION_PERIOD"
}

variable "MODULE_NAME_note" {
  type    = string
  default = ""
}

variable "MODULE_NAME_docs" {
  type    = string
  default = ""
}

variable "MODULE_NAME_filter_override" {
  type    = string
  default = ""
}

variable "MODULE_NAME_alerting_enabled" {
  type    = bool
  default = true
}

variable "MODULE_NAME_no_data_timeframe" {
  type    = number
  default = null
}

variable "MODULE_NAME_notify_no_data" {
  type    = bool
  default = false
}

variable "MODULE_NAME_ok_threshold" {
  type    = number
  default = null
}

variable "MODULE_NAME_name_prefix" {
  type    = string
  default = ""
}

variable "MODULE_NAME_name_suffix" {
  type    = string
  default = ""
}

variable "MODULE_NAME_priority" {
  description = "Number from 1 (high) to 5 (low)."

  type    = number
  default = PRIORITY
}

variable "MODULE_NAME_notification_channel_override" {
  type    = string
  default = ""
}
