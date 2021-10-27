variable "lock_waits_enabled" {
  type    = bool
  default = true
}

variable "lock_waits_warning" {
  type    = number
  default = 10.0
}

variable "lock_waits_critical" {
  type    = number
  default = 20.0
}

variable "lock_waits_evaluation_period" {
  type    = string
  default = "last_30m"
}

variable "lock_waits_note" {
  type    = string
  default = ""
}

variable "lock_waits_docs" {
  type    = string
  default = ""
}

variable "lock_waits_filter_override" {
  type    = string
  default = ""
}

variable "lock_waits_alerting_enabled" {
  type    = bool
  default = true
}

variable "lock_waits_no_data_timeframe" {
  type    = number
  default = null
}

variable "lock_waits_notify_no_data" {
  type    = bool
  default = false
}

variable "lock_waits_ok_threshold" {
  type    = number
  default = null
}

variable "lock_waits_name_prefix" {
  type    = string
  default = ""
}

variable "lock_waits_name_suffix" {
  type    = string
  default = ""
}

variable "lock_waits_priority" {
  description = "Number from 1 (high) to 5 (low)."

  type    = number
  default = 4
}