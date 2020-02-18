# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
import bpy
from bpy.types import (
    Header,
    Menu,
    Panel,
)
from bpy.app.translations import pgettext_iface as iface_
from bpy.app.translations import contexts as i18n_contexts


# -----------------------------------------------------------------------------
# Main Header

class USERPREF_HT_header(Header):
    bl_space_type = 'PREFERENCES'

    @staticmethod
    def draw_buttons(layout, context):
        prefs = context.preferences

        layout.scale_x = 1.0
        layout.scale_y = 1.0
        layout.operator_context = 'EXEC_AREA'

        row = layout.row()
        row.menu("USERPREF_MT_save_load", text="", icon='COLLAPSEMENU')

        if prefs.use_preferences_save and (not bpy.app.use_userpref_skip_save_on_exit):
            pass
        else:
            # Show '*' to let users know the preferences have been modified.
            row.operator(
                "wm.save_userpref",
                text="Save Preferences{:s}".format(" *" if prefs.is_dirty else ""),
            )

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'

        layout.template_header()

        layout.separator_spacer()
        self.draw_buttons(layout, context)


# -----------------------------------------------------------------------------
# Main Navigation Bar

class USERPREF_PT_navigation_bar(Panel):
    bl_label = "Preferences Navigation"
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'NAVIGATION_BAR'
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout

        prefs = context.preferences

        col = layout.column()

        col.scale_x = 1.3
        col.scale_y = 1.3
        col.prop(prefs, "active_section", expand=True)


class USERPREF_MT_save_load(Menu):
    bl_label = "Save & Load"

    def draw(self, context):
        layout = self.layout

        prefs = context.preferences

        row = layout.row()
        row.active = not bpy.app.use_userpref_skip_save_on_exit
        row.prop(prefs, "use_preferences_save", text="Auto-Save Preferences")

        layout.separator()

        layout.operator_context = 'EXEC_AREA'
        if prefs.use_preferences_save:
            layout.operator("wm.save_userpref", text="Save Preferences")
        sub_revert = layout.column(align=True)
        sub_revert.active = prefs.is_dirty
        sub_revert.operator("wm.read_userpref", text="Revert to Saved Preferences")

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.read_factory_userpref", text="Load Factory Preferences")


class USERPREF_PT_save_preferences(Panel):
    bl_label = "Save Preferences"
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'EXECUTE'
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        # Hide when header is visible
        for region in context.area.regions:
            if region.type == 'HEADER' and region.height <= 1:
                return True

        return False

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'

        layout.scale_x = 1.3
        layout.scale_y = 1.3

        USERPREF_HT_header.draw_buttons(layout, context)


# -----------------------------------------------------------------------------
# Min-In Helpers

# Panel mix-in.
class CenterAlignMixIn:
    """
    Base class for panels to center align contents with some horizontal margin.
    Deriving classes need to implement a ``draw_centered(context, layout)`` function.
    """

    def draw(self, context):
        layout = self.layout
        width = context.region.width
        ui_scale = context.preferences.system.ui_scale
        # No horizontal margin if region is rather small.
        is_wide = width > (350 * ui_scale)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()
        if is_wide:
            row.label()  # Needed so col below is centered.

        col = row.column()
        col.ui_units_x = 50

        # Implemented by sub-classes.
        self.draw_centered(context, col)

        if is_wide:
            row.label()  # Needed so col above is centered.


# -----------------------------------------------------------------------------
# Interface Panels

class InterfacePanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "interface"


class USERPREF_PT_interface_display(InterfacePanel, CenterAlignMixIn, Panel):
    bl_label = "Display"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        view = prefs.view

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(view, "ui_scale", text="Resolution Scale")
        flow.prop(view, "ui_line_width", text="Line Width")

        layout.separator()

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(view, "show_splash", text="Splash Screen")
        flow.prop(view, "show_tooltips")
        flow.prop(view, "show_tooltips_python")
        flow.prop(view, "show_developer_ui")
        flow.prop(view, "show_large_cursors")


class USERPREF_PT_interface_text(InterfacePanel, CenterAlignMixIn, Panel):
    bl_label = "Text Rendering"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_centered(self, context, layout):
        prefs = context.preferences
        view = prefs.view

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(view, "use_text_antialiasing", text="Anti-aliasing")
        sub = flow.column()
        sub.active = view.use_text_antialiasing
        sub.prop(view, "text_hinting", text="Hinting")

        flow.prop(view, "font_path_ui")
        flow.prop(view, "font_path_ui_mono")


class USERPREF_PT_interface_translation(InterfacePanel, CenterAlignMixIn, Panel):
    bl_label = "Translation"
    bl_translation_context = i18n_contexts.id_windowmanager

    @classmethod
    def poll(cls, context):
        return bpy.app.build_options.international

    def draw_header(self, context):
        prefs = context.preferences
        view = prefs.view

        self.layout.prop(view, "use_international_fonts", text="")

    def draw_centered(self, context, layout):
        prefs = context.preferences
        view = prefs.view

        layout.active = view.use_international_fonts

        layout.prop(view, "language")

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(view, "use_translate_tooltips", text="Tooltips")
        flow.prop(view, "use_translate_interface", text="Interface")
        flow.prop(view, "use_translate_new_dataname", text="New Data")


class USERPREF_PT_interface_editors(InterfacePanel, CenterAlignMixIn, Panel):
    bl_label = "Editors"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        view = prefs.view
        system = prefs.system

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(system, "use_region_overlap")
        flow.prop(view, "show_layout_ui", text="Corner Splitting")
        flow.prop(view, "show_navigate_ui")
        flow.prop(view, "color_picker_type")
        flow.row().prop(view, "header_align")
        flow.prop(view, "factor_display_type")


class USERPREF_PT_interface_temporary_windows(InterfacePanel, CenterAlignMixIn, Panel):
    bl_label = "Temporary Windows"
    bl_parent_id = "USERPREF_PT_interface_editors"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_centered(self, context, layout):
        prefs = context.preferences
        view = prefs.view

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(view, "render_display_type", text="Render in")
        flow.prop(view, "filebrowser_display_type", text="File Browser")


class USERPREF_PT_interface_menus(InterfacePanel, Panel):
    bl_label = "Menus"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pass


class USERPREF_PT_interface_menus_mouse_over(InterfacePanel, CenterAlignMixIn, Panel):
    bl_label = "Open on Mouse Over"
    bl_parent_id = "USERPREF_PT_interface_menus"

    def draw_header(self, context):
        prefs = context.preferences
        view = prefs.view

        self.layout.prop(view, "use_mouse_over_open", text="")

    def draw_centered(self, context, layout):
        prefs = context.preferences
        view = prefs.view

        layout.active = view.use_mouse_over_open

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(view, "open_toplevel_delay", text="Top Level")
        flow.prop(view, "open_sublevel_delay", text="Sub Level")


class USERPREF_PT_interface_menus_pie(InterfacePanel, CenterAlignMixIn, Panel):
    bl_label = "Pie Menus"
    bl_parent_id = "USERPREF_PT_interface_menus"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        view = prefs.view

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(view, "pie_animation_timeout")
        flow.prop(view, "pie_tap_timeout")
        flow.prop(view, "pie_initial_timeout")
        flow.prop(view, "pie_menu_radius")
        flow.prop(view, "pie_menu_threshold")
        flow.prop(view, "pie_menu_confirm")


# -----------------------------------------------------------------------------
# Editing Panels

class EditingPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "editing"


class USERPREF_PT_edit_objects(EditingPanel, Panel):
    bl_label = "Objects"

    def draw(self, context):
        pass


class USERPREF_PT_edit_objects_new(EditingPanel, CenterAlignMixIn, Panel):
    bl_label = "New Objects"
    bl_parent_id = "USERPREF_PT_edit_objects"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(edit, "material_link", text="Link Materials to")
        flow.prop(edit, "object_align", text="Align to")
        flow.prop(edit, "use_enter_edit_mode", text="Enter Edit Mode")


class USERPREF_PT_edit_objects_duplicate_data(EditingPanel, CenterAlignMixIn, Panel):
    bl_label = "Duplicate Data"
    bl_parent_id = "USERPREF_PT_edit_objects"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(edit, "use_duplicate_action", text="Action")
        col.prop(edit, "use_duplicate_armature", text="Armature")
        col.prop(edit, "use_duplicate_curve", text="Curve")
        # col.prop(edit, "use_duplicate_fcurve", text="F-Curve")  # Not implemented.
        col.prop(edit, "use_duplicate_light", text="Light")
        col.prop(edit, "use_duplicate_lightprobe", text="Light Probe")
        col = flow.column()
        col.prop(edit, "use_duplicate_material", text="Material")
        col.prop(edit, "use_duplicate_mesh", text="Mesh")
        col.prop(edit, "use_duplicate_metaball", text="Metaball")
        col.prop(edit, "use_duplicate_particle", text="Particle")
        col = flow.column()
        col.prop(edit, "use_duplicate_surface", text="Surface")
        col.prop(edit, "use_duplicate_text", text="Text")
        # col.prop(edit, "use_duplicate_texture", text="Texture")  # Not implemented.
        col.prop(edit, "use_duplicate_grease_pencil", text="Grease Pencil")


class USERPREF_PT_edit_cursor(EditingPanel, CenterAlignMixIn, Panel):
    bl_label = "3D Cursor"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(edit, "use_mouse_depth_cursor")
        flow.prop(edit, "use_cursor_lock_adjust")


class USERPREF_PT_edit_gpencil(EditingPanel, CenterAlignMixIn, Panel):
    bl_label = "Grease Pencil"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_centered(self, context, layout):
        prefs = context.preferences
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(edit, "grease_pencil_manhattan_distance", text="Manhattan Distance")
        flow.prop(edit, "grease_pencil_euclidean_distance", text="Euclidean Distance")


class USERPREF_PT_edit_annotations(EditingPanel, CenterAlignMixIn, Panel):
    bl_label = "Annotations"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(edit, "grease_pencil_default_color", text="Default Color")
        flow.prop(edit, "grease_pencil_eraser_radius", text="Eraser Radius")


class USERPREF_PT_edit_weight_paint(EditingPanel, CenterAlignMixIn, Panel):
    bl_label = "Weight Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_centered(self, context, layout):
        prefs = context.preferences
        view = prefs.view

        layout.prop(view, "use_weight_color_range", text="Use Custom Colors")

        col = layout.column()
        col.active = view.use_weight_color_range
        col.template_color_ramp(view, "weight_color_range", expand=True)


class USERPREF_PT_edit_misc(EditingPanel, CenterAlignMixIn, Panel):
    bl_label = "Miscellaneous"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_centered(self, context, layout):
        prefs = context.preferences
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(edit, "sculpt_paint_overlay_color", text="Sculpt Overlay Color")
        flow.prop(edit, "node_margin", text="Node Auto-offset Margin")


# -----------------------------------------------------------------------------
# Animation Panels

class AnimationPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "animation"


class USERPREF_PT_animation_timeline(AnimationPanel, CenterAlignMixIn, Panel):
    bl_label = "Timeline"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        view = prefs.view
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)
        flow.prop(edit, "use_negative_frames")

        layout.separator()

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(view, "view2d_grid_spacing_min", text="Minimum Grid Spacing")
        flow.prop(view, "timecode_style")
        flow.prop(view, "view_frame_type")
        if view.view_frame_type == 'SECONDS':
            flow.prop(view, "view_frame_seconds")
        elif view.view_frame_type == 'KEYFRAMES':
            flow.prop(view, "view_frame_keyframes")


class USERPREF_PT_animation_keyframes(AnimationPanel, CenterAlignMixIn, Panel):
    bl_label = "Keyframes"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(edit, "use_visual_keying")
        flow.prop(edit, "use_keyframe_insert_needed", text="Only Insert Needed")


class USERPREF_PT_animation_autokey(AnimationPanel, CenterAlignMixIn, Panel):
    bl_label = "Auto-Keyframing"
    bl_parent_id = "USERPREF_PT_animation_keyframes"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(edit, "use_auto_keying_warning", text="Show Warning")
        flow.prop(edit, "use_keyframe_insert_available", text="Only Insert Available")
        flow.prop(edit, "use_auto_keying", text="Enable in New Scenes")


class USERPREF_PT_animation_fcurves(AnimationPanel, CenterAlignMixIn, Panel):
    bl_label = "F-Curves"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(edit, "fcurve_unselected_alpha", text="F-Curve Visibility")
        flow.prop(edit, "fcurve_new_auto_smoothing", text="Default Smoothing Mode")
        flow.prop(edit, "keyframe_new_interpolation_type", text="Default Interpolation")
        flow.prop(edit, "keyframe_new_handle_type", text="Default Handles")
        flow.prop(edit, "use_insertkey_xyz_to_rgb", text="XYZ to RGB")


# -----------------------------------------------------------------------------
# System Panels

class SystemPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "system"


class USERPREF_PT_system_sound(SystemPanel, CenterAlignMixIn, Panel):
    bl_label = "Sound"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        system = prefs.system

        layout.prop(system, "audio_device", expand=False)

        sub = layout.grid_flow(row_major=False, columns=0, even_columns=False, even_rows=False, align=False)
        sub.active = system.audio_device not in {'NONE', 'Null'}
        sub.prop(system, "audio_channels", text="Channels")
        sub.prop(system, "audio_mixing_buffer", text="Mixing Buffer")
        sub.prop(system, "audio_sample_rate", text="Sample Rate")
        sub.prop(system, "audio_sample_format", text="Sample Format")


class USERPREF_PT_system_cycles_devices(SystemPanel, CenterAlignMixIn, Panel):
    bl_label = "Cycles Render Devices"

    def draw_centered(self, context, layout):
        prefs = context.preferences

        col = layout.column()
        col.use_property_split = False

        if bpy.app.build_options.cycles:
            addon = prefs.addons.get("cycles")
            if addon is not None:
                addon.preferences.draw_impl(col, context)
            del addon

        # NOTE: Disabled for until GPU side of OpenSubdiv is brought back.
        # system = prefs.system
        # if hasattr(system, "opensubdiv_compute_type"):
        #     col.label(text="OpenSubdiv compute:")
        #     col.row().prop(system, "opensubdiv_compute_type", text="")


class USERPREF_PT_system_memory(SystemPanel, CenterAlignMixIn, Panel):
    bl_label = "Memory & Limits"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        system = prefs.system
        edit = prefs.edit

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(edit, "undo_steps", text="Undo Steps")
        flow.prop(edit, "undo_memory_limit", text="Undo Memory Limit")
        flow.prop(edit, "use_global_undo")

        layout.separator()

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(system, "memory_cache_limit", text="Sequencer Cache Limit")
        flow.prop(system, "scrollback", text="Console Scrollback Lines")

        layout.separator()

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(system, "texture_time_out", text="Texture Time Out")
        flow.prop(system, "texture_collection_rate", text="Garbage Collection Rate")

        layout.separator()

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(system, "vbo_time_out", text="Vbo Time Out")
        flow.prop(system, "vbo_collection_rate", text="Garbage Collection Rate")


# -----------------------------------------------------------------------------
# Viewport Panels

class ViewportPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "viewport"


class USERPREF_PT_viewport_display(ViewportPanel, CenterAlignMixIn, Panel):
    bl_label = "Display"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        view = prefs.view

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(view, "show_object_info", text="Object Info")
        flow.prop(view, "show_view_name", text="View Name")
        flow.prop(view, "show_playback_fps", text="Playback FPS")

        layout.separator()

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        col = flow.column()
        col.prop(view, "gizmo_size")
        col.prop(view, "lookdev_sphere_size")

        flow.separator()

        col = flow.column()
        col.prop(view, "mini_axis_type", text="3D Viewport Axis")

        if view.mini_axis_type == 'MINIMAL':
            col.prop(view, "mini_axis_size", text="Size")
            col.prop(view, "mini_axis_brightness", text="Brightness")


class USERPREF_PT_viewport_quality(ViewportPanel, CenterAlignMixIn, Panel):
    bl_label = "Quality"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        system = prefs.system

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(system, "viewport_aa")
        flow.prop(system, "gpencil_multi_sample", text="Grease Pencil Multisampling")
        flow.prop(system, "use_overlay_smooth_wire")
        flow.prop(system, "use_edit_mode_smooth_wire")


class USERPREF_PT_viewport_textures(ViewportPanel, CenterAlignMixIn, Panel):
    bl_label = "Textures"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        system = prefs.system

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(system, "gl_texture_limit", text="Limit Size")
        flow.prop(system, "anisotropic_filter")
        flow.prop(system, "gl_clip_alpha", slider=True)
        flow.prop(system, "image_draw_method", text="Image Display Method")


class USERPREF_PT_viewport_selection(ViewportPanel, CenterAlignMixIn, Panel):
    bl_label = "Selection"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_centered(self, context, layout):
        prefs = context.preferences
        system = prefs.system

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(system, "use_select_pick_depth")


# -----------------------------------------------------------------------------
# Theme Panels

class ThemePanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "themes"


class USERPREF_MT_interface_theme_presets(Menu):
    bl_label = "Presets"
    preset_subdir = "interface_theme"
    preset_operator = "script.execute_preset"
    preset_type = 'XML'
    preset_xml_map = (
        ("preferences.themes[0]", "Theme"),
        ("preferences.ui_styles[0]", "ThemeStyle"),
    )
    draw = Menu.draw_preset

    @staticmethod
    def reset_cb(context):
        bpy.ops.preferences.reset_default_theme()


class USERPREF_PT_theme(ThemePanel, Panel):
    bl_label = "Themes"
    bl_options = {'HIDE_HEADER'}

    def draw(self, _context):
        layout = self.layout

        split = layout.split(factor=0.6)

        row = split.row(align=True)
        row.menu("USERPREF_MT_interface_theme_presets", text=USERPREF_MT_interface_theme_presets.bl_label)
        row.operator("wm.interface_theme_preset_add", text="", icon='ADD')
        row.operator("wm.interface_theme_preset_add", text="", icon='REMOVE').remove_active = True

        row = split.row(align=True)
        row.operator("preferences.theme_install", text="Install...", icon='IMPORT')
        row.operator("preferences.reset_default_theme", text="Reset", icon='LOOP_BACK')


class USERPREF_PT_theme_user_interface(ThemePanel, CenterAlignMixIn, Panel):
    bl_label = "User Interface"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _context):
        layout = self.layout

        layout.label(icon='WORKSPACE')

    def draw(self, context):
        pass


# Base class for dynamically defined widget color panels.
# This is not registered.
class PreferenceThemeWidgetColorPanel:
    bl_parent_id = "USERPREF_PT_theme_user_interface"

    def draw(self, context):
        theme = context.preferences.themes[0]
        ui = theme.user_interface
        widget_style = getattr(ui, self.wcol)
        layout = self.layout

        layout.use_property_split = True

        flow = layout.grid_flow(row_major=False, columns=2, even_columns=True, even_rows=False, align=False)

        col = flow.column(align=True)
        col.prop(widget_style, "text")
        col.prop(widget_style, "text_sel", text="Selected")
        col.prop(widget_style, "item", slider=True)

        col = flow.column(align=True)
        col.prop(widget_style, "inner", slider=True)
        col.prop(widget_style, "inner_sel", text="Selected", slider=True)
        col.prop(widget_style, "outline")

        col.separator()

        col.prop(widget_style, "roundness")


# Base class for dynamically defined widget color panels.
# This is not registered.
class PreferenceThemeWidgetShadePanel:

    def draw(self, context):
        theme = context.preferences.themes[0]
        ui = theme.user_interface
        widget_style = getattr(ui, self.wcol)
        layout = self.layout

        layout.use_property_split = True

        col = layout.column(align=True)
        col.active = widget_style.show_shaded
        col.prop(widget_style, "shadetop", text="Shade Top")
        col.prop(widget_style, "shadedown", text="Down")

    def draw_header(self, context):
        theme = context.preferences.themes[0]
        ui = theme.user_interface
        widget_style = getattr(ui, self.wcol)

        self.layout.prop(widget_style, "show_shaded", text="")


class USERPREF_PT_theme_interface_state(ThemePanel, CenterAlignMixIn, Panel):
    bl_label = "State"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "USERPREF_PT_theme_user_interface"

    def draw_centered(self, context, layout):
        theme = context.preferences.themes[0]
        ui_state = theme.user_interface.wcol_state

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        col = flow.column(align=True)
        col.prop(ui_state, "inner_anim")
        col.prop(ui_state, "inner_anim_sel")

        col = flow.column(align=True)
        col.prop(ui_state, "inner_driven")
        col.prop(ui_state, "inner_driven_sel")

        col = flow.column(align=True)
        col.prop(ui_state, "inner_key")
        col.prop(ui_state, "inner_key_sel")

        col = flow.column(align=True)
        col.prop(ui_state, "inner_overridden")
        col.prop(ui_state, "inner_overridden_sel")

        col = flow.column(align=True)
        col.prop(ui_state, "inner_changed")
        col.prop(ui_state, "inner_changed_sel")

        col = flow.column(align=True)
        col.prop(ui_state, "blend")


class USERPREF_PT_theme_interface_styles(ThemePanel, CenterAlignMixIn, Panel):
    bl_label = "Styles"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "USERPREF_PT_theme_user_interface"

    def draw_centered(self, context, layout):
        theme = context.preferences.themes[0]
        ui = theme.user_interface

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(ui, "menu_shadow_fac")
        flow.prop(ui, "icon_alpha")
        flow.prop(ui, "icon_saturation")
        flow.prop(ui, "editor_outline")
        flow.prop(ui, "widget_text_cursor")
        flow.prop(ui, "menu_shadow_width")
        flow.prop(ui, "widget_emboss")


class USERPREF_PT_theme_interface_gizmos(ThemePanel, CenterAlignMixIn, Panel):
    bl_label = "Axis & Gizmo Colors"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "USERPREF_PT_theme_user_interface"

    def draw_centered(self, context, layout):
        theme = context.preferences.themes[0]
        ui = theme.user_interface

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=False)

        col = flow.column(align=True)
        col.prop(ui, "axis_x", text="Axis X")
        col.prop(ui, "axis_y", text="Y")
        col.prop(ui, "axis_z", text="Z")

        col = flow.column()
        col.prop(ui, "gizmo_primary")
        col.prop(ui, "gizmo_secondary")

        col = flow.column()
        col.prop(ui, "gizmo_a")
        col.prop(ui, "gizmo_b")


class USERPREF_PT_theme_interface_icons(ThemePanel, CenterAlignMixIn, Panel):
    bl_label = "Icon Colors"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "USERPREF_PT_theme_user_interface"

    def draw_centered(self, context, layout):
        theme = context.preferences.themes[0]
        ui = theme.user_interface

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(ui, "icon_scene")
        flow.prop(ui, "icon_collection")
        flow.prop(ui, "icon_object")
        flow.prop(ui, "icon_object_data")
        flow.prop(ui, "icon_modifier")
        flow.prop(ui, "icon_shading")
        flow.prop(ui, "icon_folder")
        flow.prop(ui, "icon_border_intensity")


class USERPREF_PT_theme_text_style(ThemePanel, CenterAlignMixIn, Panel):
    bl_label = "Text Style"
    bl_options = {'DEFAULT_CLOSED'}

    @staticmethod
    def _ui_font_style(layout, font_style):
        layout.use_property_split = True
        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.row().prop(font_style, "font_kerning_style", expand=True)
        col.prop(font_style, "points")

        col = flow.column(align=True)
        col.prop(font_style, "shadow_offset_x", text="Shadow Offset X")
        col.prop(font_style, "shadow_offset_y", text="Y")

        col = flow.column()
        col.prop(font_style, "shadow")
        col.prop(font_style, "shadow_alpha")
        col.prop(font_style, "shadow_value")

    def draw_header(self, _context):
        layout = self.layout

        layout.label(icon='FONTPREVIEW')

    def draw_centered(self, context, layout):
        style = context.preferences.ui_styles[0]

        layout.label(text="Panel Title")
        self._ui_font_style(layout, style.panel_title)

        layout.separator()

        layout.label(text="Widget")
        self._ui_font_style(layout, style.widget)

        layout.separator()

        layout.label(text="Widget Label")
        self._ui_font_style(layout, style.widget_label)


class USERPREF_PT_theme_bone_color_sets(ThemePanel, CenterAlignMixIn, Panel):
    bl_label = "Bone Color Sets"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _context):
        layout = self.layout

        layout.label(icon='COLOR')

    def draw_centered(self, context, layout):
        theme = context.preferences.themes[0]

        layout.use_property_split = True

        for i, ui in enumerate(theme.bone_color_sets, 1):
            layout.label(text=iface_(f"Color Set {i:d}"), translate=False)

            flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

            flow.prop(ui, "normal")
            flow.prop(ui, "select")
            flow.prop(ui, "active")
            flow.prop(ui, "show_colored_constraints")


# Base class for dynamically defined theme-space panels.
# This is not registered.
class PreferenceThemeSpacePanel:

    # not essential, hard-coded UI delimiters for the theme layout
    ui_delimiters = {
        'VIEW_3D': {
            "text_grease_pencil",
            "text_keyframe",
            "speaker",
            "freestyle_face_mark",
            "split_normal",
            "bone_solid",
            "bone_locked_weight",
            "paint_curve_pivot",
        },
        'GRAPH_EDITOR': {
            "handle_vertex_select",
        },
        'IMAGE_EDITOR': {
            "paint_curve_pivot",
        },
        'NODE_EDITOR': {
            "layout_node",
        },
        'CLIP_EDITOR': {
            "handle_vertex_select",
        }
    }

    # TODO theme_area should be deprecated
    @staticmethod
    def _theme_generic(layout, themedata, theme_area):

        layout.use_property_split = True

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        props_type = {}

        for prop in themedata.rna_type.properties:
            if prop.identifier == "rna_type":
                continue

            props_type.setdefault((prop.type, prop.subtype), []).append(prop)

        th_delimiters = PreferenceThemeSpacePanel.ui_delimiters.get(theme_area)
        for props_type, props_ls in sorted(props_type.items()):
            if props_type[0] == 'POINTER':
                continue

            if th_delimiters is None:
                # simple, no delimiters
                for prop in props_ls:
                    flow.prop(themedata, prop.identifier)
            else:

                for prop in props_ls:
                    flow.prop(themedata, prop.identifier)

    def draw_header(self, _context):
        if hasattr(self, "icon") and self.icon != 'NONE':
            layout = self.layout
            layout.label(icon=self.icon)

    def draw(self, context):
        layout = self.layout
        theme = context.preferences.themes[0]

        datapath_list = self.datapath.split(".")
        data = theme
        for datapath_item in datapath_list:
            data = getattr(data, datapath_item)
        PreferenceThemeSpacePanel._theme_generic(layout, data, self.theme_area)


class ThemeGenericClassGenerator():

    @staticmethod
    def generate_panel_classes_for_wcols():
        wcols = [
            ("Regular", "wcol_regular"),
            ("Tool", "wcol_tool"),
            ("Toolbar Item", "wcol_toolbar_item"),
            ("Radio Buttons", "wcol_radio"),
            ("Text", "wcol_text"),
            ("Option", "wcol_option"),
            ("Toggle", "wcol_toggle"),
            ("Number Field", "wcol_num"),
            ("Value Slider", "wcol_numslider"),
            ("Box", "wcol_box"),
            ("Menu", "wcol_menu"),
            ("Pie Menu", "wcol_pie_menu"),
            ("Pulldown", "wcol_pulldown"),
            ("Menu Back", "wcol_menu_back"),
            ("Tooltip", "wcol_tooltip"),
            ("Menu Item", "wcol_menu_item"),
            ("Scroll Bar", "wcol_scroll"),
            ("Progress Bar", "wcol_progress"),
            ("List Item", "wcol_list_item"),
            ("Tab", "wcol_tab"),
        ]

        for (name, wcol) in wcols:
            panel_id = "USERPREF_PT_theme_interface_" + wcol
            yield type(panel_id, (PreferenceThemeWidgetColorPanel, ThemePanel, Panel), {
                "bl_label": name,
                "bl_options": {'DEFAULT_CLOSED'},
                "draw": PreferenceThemeWidgetColorPanel.draw,
                "wcol": wcol,
            })

            panel_shade_id = "USERPREF_PT_theme_interface_shade_" + wcol
            yield type(panel_shade_id, (PreferenceThemeWidgetShadePanel, ThemePanel, Panel), {
                "bl_label": "Shaded",
                "bl_options": {'DEFAULT_CLOSED'},
                "bl_parent_id": panel_id,
                "draw": PreferenceThemeWidgetShadePanel.draw,
                "wcol": wcol,
            })

    @staticmethod
    def generate_theme_area_child_panel_classes(parent_id, rna_type, theme_area, datapath):
        def generate_child_panel_classes_recurse(parent_id, rna_type, theme_area, datapath):
            props_type = {}

            for prop in rna_type.properties:
                if prop.identifier == "rna_type":
                    continue

                props_type.setdefault((prop.type, prop.subtype), []).append(prop)

            for props_type, props_ls in sorted(props_type.items()):
                if props_type[0] == 'POINTER':
                    for prop in props_ls:
                        new_datapath = datapath + "." + prop.identifier if datapath else prop.identifier
                        panel_id = parent_id + "_" + prop.identifier
                        yield type(panel_id, (PreferenceThemeSpacePanel, ThemePanel, Panel), {
                            "bl_label": rna_type.properties[prop.identifier].name,
                            "bl_parent_id": parent_id,
                            "bl_options": {'DEFAULT_CLOSED'},
                            "draw": PreferenceThemeSpacePanel.draw,
                            "theme_area": theme_area.identifier,
                            "datapath": new_datapath,
                        })

                        yield from generate_child_panel_classes_recurse(
                            panel_id,
                            prop.fixed_type,
                            theme_area,
                            new_datapath,
                        )

        yield from generate_child_panel_classes_recurse(parent_id, rna_type, theme_area, datapath)

    @staticmethod
    def generate_panel_classes_from_theme_areas():
        from bpy.types import Theme

        for theme_area in Theme.bl_rna.properties['theme_area'].enum_items_static:
            if theme_area.identifier in {'USER_INTERFACE', 'STYLE', 'BONE_COLOR_SETS'}:
                continue

            panel_id = "USERPREF_PT_theme_" + theme_area.identifier.lower()
            # Generate panel-class from theme_area
            yield type(panel_id, (PreferenceThemeSpacePanel, ThemePanel, Panel), {
                "bl_label": theme_area.name,
                "bl_options": {'DEFAULT_CLOSED'},
                "draw_header": PreferenceThemeSpacePanel.draw_header,
                "draw": PreferenceThemeSpacePanel.draw,
                "theme_area": theme_area.identifier,
                "icon": theme_area.icon,
                "datapath": theme_area.identifier.lower(),
            })

            yield from ThemeGenericClassGenerator.generate_theme_area_child_panel_classes(
                panel_id, Theme.bl_rna.properties[theme_area.identifier.lower()].fixed_type,
                theme_area, theme_area.identifier.lower())


# -----------------------------------------------------------------------------
# File Paths Panels

# Panel mix-in.
class FilePathsPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "file_paths"


class USERPREF_PT_file_paths_data(FilePathsPanel, Panel):
    bl_label = "Data"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        paths = context.preferences.filepaths

        col = self.layout.column()
        col.prop(paths, "font_directory", text="Fonts")
        col.prop(paths, "texture_directory", text="Textures")
        col.prop(paths, "script_directory", text="Scripts")
        col.prop(paths, "sound_directory", text="Sounds")
        col.prop(paths, "temporary_directory", text="Temporary Files")


class USERPREF_PT_file_paths_render(FilePathsPanel, Panel):
    bl_label = "Render"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        paths = context.preferences.filepaths

        col = self.layout.column()
        col.prop(paths, "render_output_directory", text="Render Output")
        col.prop(paths, "render_cache_directory", text="Render Cache")


class USERPREF_PT_file_paths_applications(FilePathsPanel, Panel):
    bl_label = "Applications"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        paths = context.preferences.filepaths

        col = layout.column()
        col.prop(paths, "image_editor", text="Image Editor")
        col.prop(paths, "animation_player_preset", text="Animation Player")
        if paths.animation_player_preset == 'CUSTOM':
            col.prop(paths, "animation_player", text="Player")


class USERPREF_PT_file_paths_development(FilePathsPanel, Panel):
    bl_label = "Development"

    @classmethod
    def poll(cls, context):
        prefs = context.preferences
        return prefs.view.show_developer_ui

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        paths = context.preferences.filepaths
        layout.prop(paths, "i18n_branches_directory", text="I18n Branches")


class USERPREF_PT_saveload_autorun(FilePathsPanel, Panel):
    bl_label = "Auto Run Python Scripts"
    bl_parent_id = "USERPREF_PT_saveload_blend"

    def draw_header(self, context):
        prefs = context.preferences
        paths = prefs.filepaths

        self.layout.prop(paths, "use_scripts_auto_execute", text="")

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences
        paths = prefs.filepaths

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        layout.active = paths.use_scripts_auto_execute

        box = layout.box()
        row = box.row()
        row.label(text="Excluded Paths:")
        row.operator("wm.userpref_autoexec_path_add", text="", icon='ADD', emboss=False)
        for i, path_cmp in enumerate(prefs.autoexec_paths):
            row = box.row()
            row.prop(path_cmp, "path", text="")
            row.prop(path_cmp, "use_glob", text="", icon='FILTER')
            row.operator("wm.userpref_autoexec_path_remove", text="", icon='X', emboss=False).index = i


# -----------------------------------------------------------------------------
# Save/Load Panels

class SaveLoadPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "save_load"


class USERPREF_PT_saveload_blend(SaveLoadPanel, CenterAlignMixIn, Panel):
    bl_label = "Blend Files"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        paths = prefs.filepaths
        view = prefs.view

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(paths, "use_relative_paths")
        flow.prop(paths, "use_file_compression")
        flow.prop(paths, "use_load_ui")
        flow.prop(paths, "use_save_preview_images")
        flow.prop(paths, "use_tabs_as_spaces")
        flow.prop(view, "use_save_prompt")

        layout.separator()

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(paths, "save_version")
        flow.prop(paths, "recent_files")


class USERPREF_PT_saveload_blend_autosave(SaveLoadPanel, CenterAlignMixIn, Panel):
    bl_label = "Auto Save"
    bl_parent_id = "USERPREF_PT_saveload_blend"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        paths = prefs.filepaths

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(paths, "use_auto_save_temporary_files")
        sub = flow.column()
        sub.active = paths.use_auto_save_temporary_files
        sub.prop(paths, "auto_save_time", text="Timer (mins)")


class USERPREF_PT_saveload_file_browser(SaveLoadPanel, CenterAlignMixIn, Panel):
    bl_label = "File Browser"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        paths = prefs.filepaths

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(paths, "use_filter_files")
        flow.prop(paths, "show_hidden_files_datablocks")
        flow.prop(paths, "hide_recent_locations")
        flow.prop(paths, "hide_system_bookmarks")


# -----------------------------------------------------------------------------
# Input Panels

class InputPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "input"


class USERPREF_PT_input_keyboard(InputPanel, CenterAlignMixIn, Panel):
    bl_label = "Keyboard"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        inputs = prefs.inputs

        layout.prop(inputs, "use_emulate_numpad")
        layout.prop(inputs, "use_numeric_input_advanced")


class USERPREF_PT_input_mouse(InputPanel, CenterAlignMixIn, Panel):
    bl_label = "Mouse"

    def draw_centered(self, context, layout):
        import sys
        prefs = context.preferences
        inputs = prefs.inputs

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(inputs, "use_mouse_emulate_3_button")
        if sys.platform[:3] != "win":
            rowsub = flow.row()
            rowsub.active = inputs.use_mouse_emulate_3_button
            rowsub.prop(inputs, "mouse_emulate_3_button_modifier")
        flow.prop(inputs, "use_mouse_continuous")
        flow.prop(inputs, "use_drag_immediately")
        flow.prop(inputs, "mouse_double_click_time", text="Double Click Speed")
        flow.prop(inputs, "drag_threshold_mouse")
        flow.prop(inputs, "drag_threshold_tablet")
        flow.prop(inputs, "drag_threshold")
        flow.prop(inputs, "move_threshold")


class USERPREF_PT_input_tablet(InputPanel, CenterAlignMixIn, Panel):
    bl_label = "Tablet"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        inputs = prefs.inputs

        import sys
        if sys.platform[:3] == "win":
            layout.prop(inputs, "tablet_api")
            layout.separator()

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(inputs, "pressure_threshold_max")
        flow.prop(inputs, "pressure_softness")


class USERPREF_PT_input_ndof(InputPanel, CenterAlignMixIn, Panel):
    bl_label = "NDOF"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        prefs = context.preferences
        inputs = prefs.inputs
        return inputs.use_ndof

    def draw_centered(self, context, layout):
        prefs = context.preferences
        inputs = prefs.inputs

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(inputs, "ndof_sensitivity", text="Pan Sensitivity")
        flow.prop(inputs, "ndof_orbit_sensitivity", text="Orbit Sensitivity")
        flow.prop(inputs, "ndof_deadzone", text="Deadzone")

        layout.separator()

        flow.row().prop(inputs, "ndof_view_navigate_method", expand=True)
        flow.row().prop(inputs, "ndof_view_rotate_method", expand=True)


# -----------------------------------------------------------------------------
# Navigation Panels

class NavigationPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "navigation"


class USERPREF_PT_navigation_orbit(NavigationPanel, CenterAlignMixIn, Panel):
    bl_label = "Orbit & Pan"

    def draw_centered(self, context, layout):
        import sys
        prefs = context.preferences
        inputs = prefs.inputs
        view = prefs.view

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.row().prop(inputs, "view_rotate_method", expand=True)
        if inputs.view_rotate_method == 'TURNTABLE':
            flow.prop(inputs, "view_rotate_sensitivity_turntable")
        else:
            flow.prop(inputs, "view_rotate_sensitivity_trackball")

        flow.prop(inputs, "use_rotate_around_active")
        flow.prop(inputs, "use_auto_perspective")
        flow.prop(inputs, "use_mouse_depth_navigate")
        if sys.platform == "darwin":
            flow.prop(inputs, "use_trackpad_natural", text="Natural Trackpad Direction")

        flow.separator()

        flow.prop(view, "smooth_view")
        flow.prop(view, "rotation_angle")


class USERPREF_PT_navigation_zoom(NavigationPanel, CenterAlignMixIn, Panel):
    bl_label = "Zoom"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        inputs = prefs.inputs

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.row().prop(inputs, "view_zoom_method", text="Zoom Method", expand=True)
        if inputs.view_zoom_method in {'DOLLY', 'CONTINUE'}:
            flow.row().prop(inputs, "view_zoom_axis", expand=True)
            flow.prop(inputs, "invert_mouse_zoom", text="Invert Mouse Zoom Direction")

        flow.prop(inputs, "invert_zoom_wheel", text="Invert Wheel Zoom Direction")
        # sub.prop(view, "wheel_scroll_lines", text="Scroll Lines")
        flow.prop(inputs, "use_zoom_to_mouse")


class USERPREF_PT_navigation_fly_walk(NavigationPanel, CenterAlignMixIn, Panel):
    bl_label = "Fly & Walk"

    def draw_centered(self, context, layout):
        prefs = context.preferences
        inputs = prefs.inputs

        layout.row().prop(inputs, "navigation_mode", expand=True)

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)
        flow.prop(inputs, "use_camera_lock_parent")


class USERPREF_PT_navigation_fly_walk_navigation(NavigationPanel, CenterAlignMixIn, Panel):
    bl_label = "Walk"
    bl_parent_id = "USERPREF_PT_navigation_fly_walk"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        prefs = context.preferences
        return prefs.inputs.navigation_mode == 'WALK'

    def draw_centered(self, context, layout):
        prefs = context.preferences
        inputs = prefs.inputs
        walk = inputs.walk_navigation

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(walk, "use_mouse_reverse")
        flow.prop(walk, "mouse_speed")
        flow.prop(walk, "teleport_time")

        sub = flow.column(align=True)
        sub.prop(walk, "walk_speed")
        sub.prop(walk, "walk_speed_factor")


class USERPREF_PT_navigation_fly_walk_gravity(NavigationPanel, CenterAlignMixIn, Panel):
    bl_label = "Gravity"
    bl_parent_id = "USERPREF_PT_navigation_fly_walk"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        prefs = context.preferences
        return prefs.inputs.navigation_mode == 'WALK'

    def draw_header(self, context):
        prefs = context.preferences
        inputs = prefs.inputs
        walk = inputs.walk_navigation

        self.layout.prop(walk, "use_gravity", text="")

    def draw_centered(self, context, layout):
        prefs = context.preferences
        inputs = prefs.inputs
        walk = inputs.walk_navigation

        layout.active = walk.use_gravity

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(walk, "view_height")
        flow.prop(walk, "jump_height")


# Special case, this is only exposed as a popover.
class USERPREF_PT_ndof_settings(Panel):
    bl_label = "3D Mouse Settings"
    bl_space_type = 'TOPBAR'  # dummy.
    bl_region_type = 'HEADER'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        input_prefs = context.preferences.inputs

        is_view3d = context.space_data.type == 'VIEW_3D'

        col = layout.column(align=True)
        col.prop(input_prefs, "ndof_sensitivity")
        col.prop(input_prefs, "ndof_orbit_sensitivity")
        col.prop(input_prefs, "ndof_deadzone")

        if is_view3d:
            layout.separator()
            layout.prop(input_prefs, "ndof_show_guide")

            layout.separator()
            layout.label(text="Orbit Style")
            layout.row().prop(input_prefs, "ndof_view_navigate_method", text="Navigate")
            layout.row().prop(input_prefs, "ndof_view_rotate_method", text="Orbit")
            layout.separator()

            layout.label(text="Orbit Options")
            split = layout.split(factor=0.6)
            row = split.row()
            row.alignment = 'RIGHT'
            row.label(text="Invert Axis")
            row = split.row(align=True)
            for text, attr in (
                    ("X", "ndof_rotx_invert_axis"),
                    ("Y", "ndof_roty_invert_axis"),
                    ("Z", "ndof_rotz_invert_axis"),
            ):
                row.prop(input_prefs, attr, text=text, toggle=True)

        # view2d use pan/zoom
        layout.separator()
        layout.label(text="Pan Options")

        split = layout.split(factor=0.6)
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text="Invert Axis")
        row = split.row(align=True)
        for text, attr in (
                ("X", "ndof_panx_invert_axis"),
                ("Y", "ndof_pany_invert_axis"),
                ("Z", "ndof_panz_invert_axis"),
        ):
            row.prop(input_prefs, attr, text=text, toggle=True)

        layout.prop(input_prefs, "ndof_pan_yz_swap_axis")

        layout.label(text="Zoom Options")
        layout.prop(input_prefs, "ndof_zoom_invert")

        if is_view3d:
            layout.separator()
            layout.label(text="Fly/Walk Options")
            layout.prop(input_prefs, "ndof_fly_helicopter")
            layout.prop(input_prefs, "ndof_lock_horizon")


# -----------------------------------------------------------------------------
# Key-Map Editor Panels

class KeymapPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "keymap"


class USERPREF_MT_keyconfigs(Menu):
    bl_label = "KeyPresets"
    preset_subdir = "keyconfig"
    preset_operator = "preferences.keyconfig_activate"

    def draw(self, context):
        Menu.draw_preset(self, context)


class USERPREF_PT_keymap(KeymapPanel, Panel):
    bl_label = "Keymap"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        from rna_keymap_ui import draw_keymaps

        layout = self.layout

        # import time

        # start = time.time()

        # Keymap Settings
        draw_keymaps(context, layout)

        # print("runtime", time.time() - start)


# -----------------------------------------------------------------------------
# Add-On Panels

class AddOnPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "addons"


class USERPREF_PT_addons(AddOnPanel, Panel):
    bl_label = "Add-ons"
    bl_options = {'HIDE_HEADER'}

    _support_icon_mapping = {
        'OFFICIAL': 'FILE_BLEND',
        'COMMUNITY': 'COMMUNITY',
        'TESTING': 'EXPERIMENTAL',
    }

    @staticmethod
    def is_user_addon(mod, user_addon_paths):
        import os

        if not user_addon_paths:
            for path in (
                    bpy.utils.script_path_user(),
                    bpy.utils.script_path_pref(),
            ):
                if path is not None:
                    user_addon_paths.append(os.path.join(path, "addons"))

        for path in user_addon_paths:
            if bpy.path.is_subdir(mod.__file__, path):
                return True
        return False

    @staticmethod
    def draw_error(layout, message):
        lines = message.split("\n")
        box = layout.box()
        sub = box.row()
        sub.label(text=lines[0])
        sub.label(icon='ERROR')
        for l in lines[1:]:
            box.label(text=l)

    def draw(self, context):
        import os
        import addon_utils

        layout = self.layout

        prefs = context.preferences
        used_ext = {ext.module for ext in prefs.addons}

        addon_user_dirs = tuple(
            p for p in (
                os.path.join(prefs.filepaths.script_directory, "addons"),
                bpy.utils.user_resource('SCRIPTS', "addons"),
            )
            if p
        )

        # Development option for 2.8x, don't show users bundled addons
        # unless they have been updated for 2.8x.
        # Developers can turn them on with '--debug'
        show_official_27x_addons = bpy.app.debug

        # collect the categories that can be filtered on
        addons = [
            (mod, addon_utils.module_bl_info(mod))
            for mod in addon_utils.modules(refresh=False)
        ]

        split = layout.split(factor=0.6)

        row = split.row()
        row.prop(context.window_manager, "addon_support", expand=True)

        row = split.row(align=True)
        row.operator("preferences.addon_install", icon='IMPORT', text="Install...")
        row.operator("preferences.addon_refresh", icon='FILE_REFRESH', text="Refresh")

        row = layout.row()
        row.prop(context.preferences.view, "show_addons_enabled_only")
        row.prop(context.window_manager, "addon_filter", text="")
        row.prop(context.window_manager, "addon_search", text="", icon='VIEWZOOM')

        col = layout.column()

        # set in addon_utils.modules_refresh()
        if addon_utils.error_duplicates:
            box = col.box()
            row = box.row()
            row.label(text="Multiple add-ons with the same name found!")
            row.label(icon='ERROR')
            box.label(text="Delete one of each pair to resolve:")
            for (addon_name, addon_file, addon_path) in addon_utils.error_duplicates:
                box.separator()
                sub_col = box.column(align=True)
                sub_col.label(text=addon_name + ":")
                sub_col.label(text="    " + addon_file)
                sub_col.label(text="    " + addon_path)

        if addon_utils.error_encoding:
            self.draw_error(
                col,
                "One or more addons do not have UTF-8 encoding\n"
                "(see console for details)",
            )

        show_enabled_only = context.preferences.view.show_addons_enabled_only
        filter = context.window_manager.addon_filter
        search = context.window_manager.addon_search.lower()
        support = context.window_manager.addon_support

        # initialized on demand
        user_addon_paths = []

        for mod, info in addons:
            module_name = mod.__name__

            is_enabled = module_name in used_ext

            if info["support"] not in support:
                continue

            # check if addon should be visible with current filters
            is_visible = (
                (filter == "All") or
                (filter == info["category"]) or
                (filter == "User" and (mod.__file__.startswith(addon_user_dirs)))
            )
            if show_enabled_only:
                is_visible = is_visible and is_enabled

            if is_visible:
                if search and search not in info["name"].lower():
                    if info["author"]:
                        if search not in info["author"].lower():
                            continue
                    else:
                        continue

                # Skip 2.7x add-ons included with Blender, unless in debug mode.
                is_addon_27x = info.get("blender", (0,)) < (2, 80)
                if (
                        is_addon_27x and
                        (not show_official_27x_addons) and
                        (not mod.__file__.startswith(addon_user_dirs))
                ):
                    continue

                # Addon UI Code
                col_box = col.column()
                box = col_box.box()
                colsub = box.column()
                row = colsub.row(align=True)

                row.operator(
                    "preferences.addon_expand",
                    icon='DISCLOSURE_TRI_DOWN' if info["show_expanded"] else 'DISCLOSURE_TRI_RIGHT',
                    emboss=False,
                ).module = module_name

                row.operator(
                    "preferences.addon_disable" if is_enabled else "preferences.addon_enable",
                    icon='CHECKBOX_HLT' if is_enabled else 'CHECKBOX_DEHLT', text="",
                    emboss=False,
                ).module = module_name

                sub = row.row()
                sub.active = is_enabled
                sub.label(text="%s: %s" % (info["category"], info["name"]))

                # WARNING: 2.8x exception, may be removed
                # use disabled state for old add-ons, chances are they are broken.
                if is_addon_27x:
                    sub.label(text="Upgrade to 2.8x required")
                    sub.label(icon='ERROR')
                # Remove code above after 2.8x migration is complete.
                elif info["warning"]:
                    sub.label(icon='ERROR')

                # icon showing support level.
                sub.label(icon=self._support_icon_mapping.get(info["support"], 'QUESTION'))

                # Expanded UI (only if additional info is available)
                if info["show_expanded"]:
                    if info["description"]:
                        split = colsub.row().split(factor=0.15)
                        split.label(text="Description:")
                        split.label(text=info["description"])
                    if info["location"]:
                        split = colsub.row().split(factor=0.15)
                        split.label(text="Location:")
                        split.label(text=info["location"])
                    if mod:
                        split = colsub.row().split(factor=0.15)
                        split.label(text="File:")
                        split.label(text=mod.__file__, translate=False)
                    if info["author"]:
                        split = colsub.row().split(factor=0.15)
                        split.label(text="Author:")
                        split.label(text=info["author"], translate=False)
                    if info["version"]:
                        split = colsub.row().split(factor=0.15)
                        split.label(text="Version:")
                        split.label(text=".".join(str(x) for x in info["version"]), translate=False)
                    if info["warning"]:
                        split = colsub.row().split(factor=0.15)
                        split.label(text="Warning:")
                        split.label(text="  " + info["warning"], icon='ERROR')

                    user_addon = USERPREF_PT_addons.is_user_addon(mod, user_addon_paths)
                    tot_row = bool(info["wiki_url"]) + bool(user_addon)

                    if tot_row:
                        split = colsub.row().split(factor=0.15)
                        split.label(text="Internet:")
                        sub = split.row()
                        if info["wiki_url"]:
                            sub.operator(
                                "wm.url_open", text="Documentation", icon='HELP',
                            ).url = info["wiki_url"]
                        # Only add "Report a Bug" button if tracker_url is set
                        # or the add-on is bundled (use official tracker then).
                        if info.get("tracker_url"):
                            sub.operator(
                                "wm.url_open", text="Report a Bug", icon='URL',
                            ).url = info["tracker_url"]
                        elif not user_addon:
                            addon_info = ("Name: {} {}\nAuthor: {}\n").format(
                                info["name"], info["version"], info["author"])
                            props = sub.operator(
                                "wm.url_open_preset", text="Report a Bug", icon='URL',
                            )
                            props.type = 'BUG_ADDON'
                            props.id = addon_info
                        if user_addon:
                            sub.operator(
                                "preferences.addon_remove", text="Remove", icon='CANCEL',
                            ).module = mod.__name__

                    # Show addon user preferences
                    if is_enabled:
                        addon_preferences = prefs.addons[module_name].preferences
                        if addon_preferences is not None:
                            draw = getattr(addon_preferences, "draw", None)
                            if draw is not None:
                                addon_preferences_class = type(addon_preferences)
                                box_prefs = col_box.box()
                                box_prefs.label(text="Preferences:")
                                addon_preferences_class.layout = box_prefs
                                try:
                                    draw(context)
                                except:
                                    import traceback
                                    traceback.print_exc()
                                    box_prefs.label(text="Error (see console)", icon='ERROR')
                                del addon_preferences_class.layout

        # Append missing scripts
        # First collect scripts that are used but have no script file.
        module_names = {mod.__name__ for mod, info in addons}
        missing_modules = {ext for ext in used_ext if ext not in module_names}

        if missing_modules and filter in {"All", "Enabled"}:
            col.column().separator()
            col.column().label(text="Missing script files")

            module_names = {mod.__name__ for mod, info in addons}
            for module_name in sorted(missing_modules):
                is_enabled = module_name in used_ext
                # Addon UI Code
                box = col.column().box()
                colsub = box.column()
                row = colsub.row(align=True)

                row.label(text="", icon='ERROR')

                if is_enabled:
                    row.operator(
                        "preferences.addon_disable", icon='CHECKBOX_HLT', text="", emboss=False,
                    ).module = module_name

                row.label(text=module_name, translate=False)


# -----------------------------------------------------------------------------
# Studio Light Panels

class StudioLightPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "lights"


class StudioLightPanelMixin:

    def _get_lights(self, prefs):
        return [light for light in prefs.studio_lights if light.is_user_defined and light.type == self.sl_type]

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences
        lights = self._get_lights(prefs)

        self.draw_light_list(layout, lights)

    def draw_light_list(self, layout, lights):
        if lights:
            flow = layout.grid_flow(row_major=False, columns=4, even_columns=True, even_rows=True, align=False)
            for studio_light in lights:
                self.draw_studio_light(flow, studio_light)
        else:
            layout.label(text="No custom {} configured".format(self.bl_label))

    def draw_studio_light(self, layout, studio_light):
        box = layout.box()
        row = box.row()

        row.template_icon(layout.icon(studio_light), scale=3.0)
        col = row.column()
        op = col.operator("preferences.studiolight_uninstall", text="", icon='REMOVE')
        op.index = studio_light.index

        if studio_light.type == 'STUDIO':
            op = col.operator("preferences.studiolight_copy_settings", text="", icon='IMPORT')
            op.index = studio_light.index

        box.label(text=studio_light.name)


class USERPREF_PT_studiolight_matcaps(StudioLightPanel, StudioLightPanelMixin, Panel):
    bl_label = "MatCaps"
    sl_type = 'MATCAP'

    def draw_header_preset(self, _context):
        layout = self.layout
        layout.operator("preferences.studiolight_install", icon='IMPORT', text="Install...").type = 'MATCAP'
        layout.separator()


class USERPREF_PT_studiolight_world(StudioLightPanel, StudioLightPanelMixin, Panel):
    bl_label = "HDRIs"
    sl_type = 'WORLD'

    def draw_header_preset(self, _context):
        layout = self.layout
        layout.operator("preferences.studiolight_install", icon='IMPORT', text="Install...").type = 'WORLD'
        layout.separator()


class USERPREF_PT_studiolight_lights(StudioLightPanel, StudioLightPanelMixin, Panel):
    bl_label = "Studio Lights"
    sl_type = 'STUDIO'

    def draw_header_preset(self, _context):
        layout = self.layout
        op = layout.operator("preferences.studiolight_install", icon='IMPORT', text="Install...")
        op.type = 'STUDIO'
        op.filter_glob = ".sl"
        layout.separator()


class USERPREF_PT_studiolight_light_editor(StudioLightPanel, Panel):
    bl_label = "Editor"
    bl_parent_id = "USERPREF_PT_studiolight_lights"
    bl_options = {'DEFAULT_CLOSED'}

    @staticmethod
    def opengl_light_buttons(layout, light):

        col = layout.column()
        col.active = light.use

        col.prop(light, "use", text="Use Light")
        col.prop(light, "diffuse_color", text="Diffuse")
        col.prop(light, "specular_color", text="Specular")
        col.prop(light, "smooth")
        col.prop(light, "direction")

    def draw(self, context):
        layout = self.layout

        prefs = context.preferences
        system = prefs.system

        row = layout.row()
        row.prop(system, "use_studio_light_edit", toggle=True)
        row.operator("preferences.studiolight_new", text="Save as Studio light", icon='FILE_TICK')

        layout.separator()

        layout.use_property_split = True
        column = layout.split()
        column.active = system.use_studio_light_edit

        light = system.solid_lights[0]
        colsplit = column.split(factor=0.85)
        self.opengl_light_buttons(colsplit, light)

        light = system.solid_lights[1]
        colsplit = column.split(factor=0.85)
        self.opengl_light_buttons(colsplit, light)

        light = system.solid_lights[2]
        colsplit = column.split(factor=0.85)
        self.opengl_light_buttons(colsplit, light)

        light = system.solid_lights[3]
        self.opengl_light_buttons(column, light)

        layout.separator()

        layout.prop(system, "light_ambient")


# -----------------------------------------------------------------------------
# Experimental Panels

class ExperimentalPanel:
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "experimental"

    url_prefix = "https://developer.blender.org/"

"""
# Example panel, leave it here so we always have a template to follow even
# after the features are gone from the experimental panel.

class USERPREF_PT_experimental_virtual_reality(ExperimentalPanel, Panel):
    bl_label = "Virtual Reality"

    def draw(self, context):
        prefs = context.preferences
        experimental = prefs.experimental

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        task = "T71347"
        split = layout.split(factor=0.66)
        col = split.split()
        col.prop(experimental, "use_virtual_reality_scene_inspection", text="Scene Inspection")
        col = split.split()
        col.operator("wm.url_open", text=task, icon='URL').url = self.url_prefix + task

        task = "T71348"
        split = layout.split(factor=0.66)
        col = split.column()
        col.prop(experimental, "use_virtual_reality_immersive_drawing", text="Continuous Immersive Drawing")
        col = split.column()
        col.operator("wm.url_open", text=task, icon='URL').url = self.url_prefix + task
"""


# -----------------------------------------------------------------------------
# Class Registration

# Order of registration defines order in UI,
# so dynamically generated classes are 'injected' in the intended order.
classes = (
    USERPREF_PT_theme_user_interface,
    *ThemeGenericClassGenerator.generate_panel_classes_for_wcols(),
    USERPREF_HT_header,
    USERPREF_PT_navigation_bar,
    USERPREF_PT_save_preferences,
    USERPREF_MT_save_load,

    USERPREF_PT_interface_display,
    USERPREF_PT_interface_editors,
    USERPREF_PT_interface_temporary_windows,
    USERPREF_PT_interface_translation,
    USERPREF_PT_interface_text,
    USERPREF_PT_interface_menus,
    USERPREF_PT_interface_menus_mouse_over,
    USERPREF_PT_interface_menus_pie,

    USERPREF_PT_viewport_display,
    USERPREF_PT_viewport_quality,
    USERPREF_PT_viewport_textures,
    USERPREF_PT_viewport_selection,

    USERPREF_PT_edit_objects,
    USERPREF_PT_edit_objects_new,
    USERPREF_PT_edit_objects_duplicate_data,
    USERPREF_PT_edit_cursor,
    USERPREF_PT_edit_annotations,
    USERPREF_PT_edit_weight_paint,
    USERPREF_PT_edit_gpencil,
    USERPREF_PT_edit_misc,

    USERPREF_PT_animation_timeline,
    USERPREF_PT_animation_keyframes,
    USERPREF_PT_animation_autokey,
    USERPREF_PT_animation_fcurves,

    USERPREF_PT_system_cycles_devices,
    USERPREF_PT_system_memory,
    USERPREF_PT_system_sound,

    USERPREF_MT_interface_theme_presets,
    USERPREF_PT_theme,
    USERPREF_PT_theme_interface_state,
    USERPREF_PT_theme_interface_styles,
    USERPREF_PT_theme_interface_gizmos,
    USERPREF_PT_theme_interface_icons,
    USERPREF_PT_theme_text_style,
    USERPREF_PT_theme_bone_color_sets,

    USERPREF_PT_file_paths_data,
    USERPREF_PT_file_paths_render,
    USERPREF_PT_file_paths_applications,
    USERPREF_PT_file_paths_development,

    USERPREF_PT_saveload_blend,
    USERPREF_PT_saveload_blend_autosave,
    USERPREF_PT_saveload_autorun,
    USERPREF_PT_saveload_file_browser,

    USERPREF_MT_keyconfigs,

    USERPREF_PT_input_keyboard,
    USERPREF_PT_input_mouse,
    USERPREF_PT_input_tablet,
    USERPREF_PT_input_ndof,
    USERPREF_PT_navigation_orbit,
    USERPREF_PT_navigation_zoom,
    USERPREF_PT_navigation_fly_walk,
    USERPREF_PT_navigation_fly_walk_navigation,
    USERPREF_PT_navigation_fly_walk_gravity,

    USERPREF_PT_keymap,
    USERPREF_PT_addons,

    USERPREF_PT_studiolight_lights,
    USERPREF_PT_studiolight_light_editor,
    USERPREF_PT_studiolight_matcaps,
    USERPREF_PT_studiolight_world,

    # Popovers.
    USERPREF_PT_ndof_settings,

    # Add dynamically generated editor theme panels last,
    # so they show up last in the theme section.
    *ThemeGenericClassGenerator.generate_panel_classes_from_theme_areas(),
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
