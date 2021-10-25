variable "filter_str" {
  type = string
}

variable "env" {
  type = string
}

variable "service" {
  type    = string
  default = "SERVICE_NAME"
}

variable "notification_channel" {
  type = string
}

variable "additional_tags" {
  type    = list(string)
  default = []
}

variable "locked" {
  type    = bool
  default = true
}

variable "name_prefix" {
  type    = string
  default = ""
}

variable "name_suffix" {
  type    = string
  default = ""
}

variable "service_check_include_tags" {
  description = "Tags to be included in the \"over\" section of a service check query"
  type        = list(string)
}

variable "service_check_exclude_tags" {
  description = "Tags to be included in the \"exclude\" section of a service check query"

  type    = list(string)
  default = []
}