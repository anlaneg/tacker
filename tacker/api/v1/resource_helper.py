# (c) Copyright 2014 Cisco Systems Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg

from tacker.api import extensions
from tacker.api.v1 import base
from tacker import manager
from tacker.plugins.common import constants


def build_plural_mappings(special_mappings, resource_map):
    """Create plural to singular mapping for all resources.

    Allows for special mappings to be provided, like policies -> policy.
    Otherwise, will strip off the last character for normal mappings, like
    routers -> router.
    """
    plural_mappings = {}
    #遍历资源的每个配置项
    for plural in resource_map:
        #在sepcial_mappings中找plural,如果未找到，返回plural截掉's'后的字符串
        singular = special_mappings.get(plural, plural[:-1])
        #将singular加入
        plural_mappings[plural] = singular
    return plural_mappings


def build_resource_info(plural_mappings, resource_map, which_service,
                        action_map=None,
                        translate_name=False, allow_bulk=False):
    """Build resources for advanced services.

    Takes the resource information, and singular/plural mappings, and creates
    API resource objects for advanced services extensions. Will optionally
    translate underscores to dashes in resource names, register the resource,
    and accept action information for resources.

    :param plural_mappings: mappings between singular and plural forms
    :param resource_map: attribute map for the WSGI resources to create
    :param which_service: The name of the service for which the WSGI resources
                          are being created. This name will be used to pass
                          the appropriate plugin to the WSGI resource.
                          It can be set to None or "CORE"to create WSGI
                          resources for the core plugin
    :param action_map: custom resource actions
    :param translate_name: replaces underscores with dashes
    :param allow_bulk: True if bulk create are allowed
    """
    resources = []
    #指明使用哪个服务插件
    if not which_service:
        which_service = constants.CORE
    action_map = action_map or {}
    #取对应的报务插件
    plugin = manager.TackerManager.get_service_plugins()[which_service]
    for collection_name in resource_map:
        #取资源名称
        resource_name = plural_mappings[collection_name]
        #取资源属性
        params = resource_map.get(collection_name, {})
        if translate_name:
            #名称规范化
            collection_name = collection_name.replace('_', '-')
        member_actions = action_map.get(resource_name, {})
        #创建controller
        controller = base.create_resource(
            collection_name, resource_name, plugin, params,
            member_actions=member_actions,
            allow_bulk=allow_bulk,
            allow_pagination=cfg.CONF.allow_pagination,
            allow_sorting=cfg.CONF.allow_sorting)
        #创建resource
        resource = extensions.ResourceExtension(
            collection_name,
            controller,#负责此资源的controller
            path_prefix=constants.COMMON_PREFIXES[which_service],#不同服务对应的前缀
            member_actions=member_actions,
            attr_map=params)
        resources.append(resource)
    return resources
