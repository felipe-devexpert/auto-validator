from django.contrib import admin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import path, reverse
from django.urls.resolvers import URLPattern
from rest_framework.authtoken.admin import TokenAdmin

from auto_validator.core.models import (
    Hotkey,
    Operator,
    Server,
    Subnet,
    SubnetSlot,
    UploadedFile,
    ValidatorInstance,
)
from auto_validator.core.utils.utils import fetch_and_compare_subnets, install_validator_on_remote_server

from auto_validator.core.plugins.plugin_manager import PluginManager
from auto_validator.core.plugins.linode_plugin import LinodePlugin
from auto_validator.core.plugins.paperspace_plugin import PaperspacePlugin
from auto_validator.core.plugins.digitalocean_plugin import DigitalOceanPlugin
from auto_validator.core.plugins.oblivus_plugin import OblivusPlugin
from auto_validator.core.plugins.runpod_plugin import RunPodPlugin
from auto_validator.core.plugins.self_managed_plugin import SelfManagedPlugin

plugin_manager = PluginManager()
plugin_manager.register_plugin('Linode', LinodePlugin)
plugin_manager.register_plugin('Paperspace', PaperspacePlugin)
plugin_manager.register_plugin('DigitalOcean', DigitalOceanPlugin)
plugin_manager.register_plugin('Oblivus', OblivusPlugin)
plugin_manager.register_plugin('RunPod', RunPodPlugin)
plugin_manager.register_plugin('SelfManaged', SelfManagedPlugin)

admin.site.site_header = "auto_validator Administration"
admin.site.site_title = "auto_validator"
admin.site.index_title = "Welcome to auto_validator Administration"

TokenAdmin.raw_id_fields = ["user"]


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ("file_name", "file_size", "hotkey", "description", "created_at")
    list_filter = ("hotkey", "created_at", "file_size")
    search_fields = ("file_name",)


@admin.register(Subnet)
class SubnetAdmin(admin.ModelAdmin):
    list_display = (
        "codename",
        "mainnet_netuid",
        "testnet_netuid",
        "owner_nick",
        "registered_networks",
    )
    search_fields = ("name", "slots__netuid")

    def create_server(self, request, queryset):
        subnet = queryset.first()
        return redirect("admin:select_provider", subnet_id=subnet.id)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("sync-subnets/", self.admin_site.admin_view(self.sync_subnet), name="sync_subnets"),        ]
        return custom_urls + urls

    def sync_subnet(self, request):
        return fetch_and_compare_subnets(request)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["sync_subnets_url"] = reverse("admin:sync_subnets")
        return super().changelist_view(request, extra_context=extra_context)
    

@admin.register(SubnetSlot)
class SubnetSlotAdmin(admin.ModelAdmin):
    list_display = (
        "subnet",
        "blockchain",
        "netuid",
        "is_registered",
        "max_registration_price_RAO",
        "registration_block",
        "deregistration_block",
    )
    search_fields = ("subnet__name", "netuid")
    list_filter = ("blockchain",)
    list_select_related = ("subnet", "registration_block", "deregistration_block")
    
    def get_urls(self) -> list[URLPattern]:
        custom_urls = [
            path("install-validator/<int:subnet_uid>", self.admin_site.admin_view(self.install_validator_view), name="install_validator"),
            path("install-validator/create-server/<str:provider>/<int:subnet_uid>", self.admin_site.admin_view(self.create_server_view), name="create_server")
        ]
        return super().get_urls() + custom_urls
    
    def install_validator_view(self, request, subnet_uid):
        subnet_slot = get_object_or_404(SubnetSlot, netuid=subnet_uid)
        providers = plugin_manager.get_registered_plugins()
        
        # Handle search query
        search_query = request.GET.get('search', '')
        if search_query:
            providers = [provider for provider in providers if search_query.lower() in provider.lower()]
        
        # Handle sorting query
        sort_query = request.GET.get('sort', 'name')  # Default sort by name
        if sort_query == 'name':
            providers.sort(key=lambda x: x.lower())
        elif sort_query == 'reverse_name':
            providers.sort(key=lambda x: x.lower(), reverse=True)
        paginator = Paginator(providers, 9)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        
        if request.method == "POST":
            provider = request.POST.get("provider")
            self.message_user(request, f'{provider} selected')
            return redirect('admin:create_server', provider=provider, subnet_uid=subnet_uid)
        
        context = {
            "page_obj": page_obj,
            "search_query": search_query,
            "sort_query": sort_query,
            "subnet_uid": subnet_slot.netuid,
            "subnet_name": subnet_slot.subnet.name,
        }
        return render(request, "admin/select_provider.html", context)
        
    def create_server_view(self, request, provider, subnet_uid):
        subnet_slot = get_object_or_404(SubnetSlot, netuid=subnet_uid)
        plugin = plugin_manager.get_plugin(provider)
        if request.method == 'POST':
            form_data = request.POST.copy()
            form_data["api_key"] = "1234"
            form_info = {}
            for key, value in form_data.items():
                form_info[key] = value
            print(form_info)
            result = plugin.create_machine(form_info)
            if result.get("status") == "success":
                self.message_user(request, "Server created successfully")
            else:
                self.message_user(request, result.get("data"), level="error")
            return redirect('admin:core_subnetslot_changelist')
        machines_result = plugin.list_available_machines()
        regions_result = plugin.list_available_regions()
        
        if machines_result.get("status") == "success" and regions_result.get("status") == "success":
            machines_list = machines_result.get("data")
            regions_list = regions_result.get("data")
            
            # Pagination for machines
            machines_paginator = Paginator(machines_list, 10)
            machines_page = request.GET.get('machines_page')
            try:
                machines = machines_paginator.page(machines_page)
            except PageNotAnInteger:
                machines = machines_paginator.page(1)
            except EmptyPage:
                machines = machines_paginator.page(machines_paginator.num_pages)
            
            # Pagination for regions
            regions_paginator = Paginator(regions_list, 10)
            regions_page = request.GET.get('regions_page')
            try:
                regions = regions_paginator.page(regions_page)
            except PageNotAnInteger:
                regions = regions_paginator.page(1)
            except EmptyPage:
                regions = regions_paginator.page(regions_paginator.num_pages)
            
            context = {
                "fields": plugin.get_required_fields(),
                "provider": provider,
                "regions_list": regions,
                "machines_list": machines,
                "subnet_hw_requirements": subnet_slot.subnet.hardware_description
            }
        else:
            self.message_user(request, machines_result.get("data"), level="error")
        return render(request, 'admin/create_server.html', context)

    def registration_block(self, obj):
        return obj.registration_block.serial_number if obj.registration_block else "N/A"

    def deregistration_block(self, obj):
        return obj.deregistration_block.serial_number if obj.deregistration_block else "N/A"
    
    registration_block.short_description = "Registration Block"
    deregistration_block.short_description = "Deregistration Block"

    def max_registration_price_RAO(self, obj):
        return f"{obj.maximum_registration_price} RAO"

    def is_registered(self, obj):
        return obj.registration_block is not None and obj.deregistration_block is None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            is_registered_sort=Case(
                When(registration_block__isnull=False, deregistration_block__isnull=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        return qs.order_by("blockchain", "netuid")

    is_registered.boolean = True
    is_registered.admin_order_field = "is_registered_sort"
    is_registered.short_description = "Is Registered"

    def install_validator_action(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one subnet slot.", level="ERROR")
            return
        subnet_slot = queryset.first()
        return redirect("admin:install_validator", subnet_uid=subnet_slot.netuid)
        # install_validator_on_remote_server(
        #     subnet_slot.subnet.codename,
        #     subnet_slot.blockchain,
        #     subnet_slot.netuid,
        #     "172.236.101.138",
        #     "root",
        #     "/root/.ssh/id_rsa",
        #     "1234567890",
        # )
    install_validator_action.short_description = "Install Validator"
    actions = ["install_validator_action"]


@admin.register(ValidatorInstance)
class ValidatorInstanceAdmin(admin.ModelAdmin):
    list_display = ("subnet_slot", "hotkey", "last_updated", "status", "server", "created_at")
    search_fields = ("hotkey", "subnet_slot__subnet__name", "server__name")
    
    def uninstall_validator(self, request, queryset):
        for instance in queryset:
            # implememt uninstallation logic here
            # if validator is successfully uninstalled, show success message
            # if validator is not uninstalled, show error message
            
            # instance.server.validator_instances.clear()
            # instance.delete()
            pass
    
    def restart_validator(self, request, queryset):
        for instance in queryset:
            # implememt restart logic here
            # if validator is successfully restarted, show success message
            # if validator is not restarted, show error message
            pass
    
    def stop_validator(self, request, queryset):
        for instance in queryset:
            # implememt stop logic here
            # if validator is successfully stopped, show success message
            # if validator is not stopped, show error message
            pass
    
    def start_validator(self, request, queryset):
        for instance in queryset:
            # implememt start logic here
            # if validator is successfully started, show success message
            # if validator is not started, show error message
            pass
    
    def update_validator(self, request, queryset):
        for instance in queryset:
            # implememt update logic here
            # if validator is successfully updated, show success message
            # if validator is not updated, show error message
            pass
    
    
    actions = ["uninstall_validator", "restart_validator", "stop_validator", "start_validator", "update_validator"]


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("name", "ip_address", "subnet_slot", "validatorinstance_status", "description", "created_at")
    search_fields = ("name", "ip_address", "validator_instances__subnet_slot__subnet__name")

    def subnet_slot(self, obj):
        return obj.validator_instances.subnet_slot if obj.validator_instances else "N/A"

    def validatorinstance_status(self, obj):
        return getattr(obj.validator_instances, "status", False)

    validatorinstance_status.boolean = True

    list_select_related = ("validator_instances", "validator_instances__subnet_slot")


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ("name", "discord_id")
    search_fields = ("name", "discord_id")


@admin.register(Hotkey)
class HotkeyAdmin(admin.ModelAdmin):
    list_display = ("hotkey", "is_mother")
    search_fields = ("hotkey",)
