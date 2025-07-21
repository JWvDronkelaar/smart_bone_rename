import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from mathutils import Vector
import random, string

def get_bone_head_position(bone, mode):
    if mode == 'EDIT':
        return bone.head
    elif mode == 'POSE':
        return bone.bone.head_local
    return Vector((0, 0, 0))

def generate_dummy_name():
    return "DUMMY_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class RenameBonesByProximityOperator(Operator):
    bl_idname = "armature.rename_bones_by_proximity"
    bl_label = "Rename Bones by Proximity"
    bl_options = {'REGISTER', 'UNDO'}

    base_name: StringProperty(name="Base Name", default="Bone")

    def draw(self, context):
        self.layout.prop(self, "base_name")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def execute(self, context):
        obj = context.object
        mode = obj.mode

        if not obj or obj.type != 'ARMATURE' or mode not in {'EDIT'}:
            self.report({'ERROR'}, "Must be in Edit Mode with an armature selected")
            return {'CANCELLED'}

        if mode == 'EDIT':
            bones = obj.data.edit_bones
            selected = [b for b in bones if b.select]
            active = bones.active

        if not active or active not in selected:
            self.report({'ERROR'}, "Select bones and set an active one.")
            return {'CANCELLED'}

        total = len(selected)

        if total <= 1:
                self.report({'ERROR'}, "Please select two or more bones.")
                return {'CANCELLED'}

        new_names = {f"{self.base_name}_{i+1:03d}" for i in range(total)}
        existing = {b.name for b in obj.data.edit_bones if b not in selected}

        if new_names & existing:
            self.report({'ERROR'}, "One or more target names already exist.")
            return {'CANCELLED'}

        dummy_names = {}
        for bone in selected:
            dummy_name = generate_dummy_name()
            while dummy_name in obj.data.bones:
                dummy_name = generate_dummy_name()
            dummy_names[bone] = dummy_name
            bone.name = dummy_name # TODO: this is edit mode only

        positions = {b: get_bone_head_position(b, mode) for b in selected}
        unvisited = set(selected)
        current = active
        index = 1

        while unvisited:
            new_name = f"{self.base_name}_{index:03d}"
            current.name = new_name # TODO: this is edit mode only
            unvisited.remove(current)
            index += 1
            if unvisited:
                current_pos = positions[current]
                current = min(unvisited, key=lambda b: (positions[b] - current_pos).length)

        self.report({'INFO'}, "Renaming complete.")
        return {'FINISHED'}

def draw_context_menu(self, context):
    self.layout.operator(RenameBonesByProximityOperator.bl_idname)

def register():
    bpy.utils.register_class(RenameBonesByProximityOperator)

def unregister():
    bpy.utils.unregister_class(RenameBonesByProximityOperator)

if __name__ == "__main__":
    register()
