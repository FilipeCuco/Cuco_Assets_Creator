bl_info = {
    "name": "Cuco Assets Creator",
    "description": "Create Assets to GTA V.",
    "author": "Filipe Cuco",
    "version": (1, 0),
    "blender": (4, 2, 0),
}

import bpy
import re

def remove_object_and_children(obj, removed_objects):
    """Remove o objeto e todos os seus filhos de forma recursiva."""
    for child in list(obj.children):
        if child not in removed_objects:
            remove_object_and_children(child, removed_objects)
    if obj not in removed_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
        removed_objects.add(obj)

def merge_objects(objects_to_merge, new_name):
    """Mescla uma lista de objetos em um novo objeto e remove o parent original."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects_to_merge:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

    if len(objects_to_merge) > 1:
        bpy.ops.object.join()
        new_obj = bpy.context.active_object
        if new_obj:
            new_obj.name = new_name
            new_obj.parent = None
            return new_obj
    return None

def cuco_convert_to_asset():
    """Converte e remove ativos conforme especificado."""
    try:
        objects = list(bpy.context.scene.objects)
        potential_parents = []
        objects_to_remove = []

        for obj in objects:
            if obj.sollum_type and len(obj.children) > 0:
                potential_parents.append(obj)

        first_parents = [obj for obj in potential_parents if obj.parent is None]

        removed_objects = set()

        for first_parent in first_parents:
            if first_parent.sollum_type == "sollumz_drawable":
                for obj in list(first_parent.children):
                    if obj.sollum_type == "sollumz_bound_box":
                        objects_to_remove.append(obj)
                    
                    if obj.name.endswith(".model") or obj.sollum_type != "sollumz_bound_box":
                        obj.parent = None
                        obj.name = first_parent.name
                        obj.asset_mark()
                        obj.asset_generate_preview()
                        if not hasattr(obj, "asset_data") or not obj.asset_data:
                            objects_to_remove.append(obj)

                objects_to_remove.append(first_parent)

            elif first_parent.sollum_type == "sollumz_fragment":
                for child in list(first_parent.children):
                    if child.name.endswith(".col"):
                        remove_object_and_children(child, removed_objects)
                    elif child.name.endswith(".mesh"):
                        drawable_models = [c for c in child.children if c.sollum_type == "sollumz_drawable_model"]
                        if len(drawable_models) > 1:
                            merged_obj = merge_objects(drawable_models, child.name)
                            if merged_obj:
                                merged_obj.name = first_parent.name
                                merged_obj.asset_mark()
                                merged_obj.asset_generate_preview()
                            objects_to_remove.append(child)
                        else:
                            for model in drawable_models:
                                model.name = first_parent.name
                                model.asset_mark()
                                model.asset_generate_preview()
                                objects_to_remove.append(model)

                objects_to_remove.append(first_parent)

        # Remover objetos apenas uma vez
        for obj in objects_to_remove:
            if obj not in removed_objects:
                remove_object_and_children(obj, removed_objects)

        cuco_asset_remove_suffix()

    except Exception as e:
        print(f"Erro durante a conversão para asset: {e}")

def cuco_asset_remove_suffix():
    """Remove numeric suffixes from object names."""
    for obj in bpy.context.scene.objects:
        new_name = re.sub(r"\.\d+$", "", obj.name)
        if new_name != obj.name:
            obj.name = new_name

class ConvertToGTAVAsset(bpy.types.Operator):
    """Run the Cuco Assets Creator script"""
    bl_idname = "object.cuco_assets_creator"
    bl_label = "Convert to GTA V Asset"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.view_layer.update()
        cuco_convert_to_asset()
        return {"FINISHED"}

class CucoAssetsCreatorPanel(bpy.types.Panel):
    """Cuco Assets Creator Panel"""
    bl_label = "Cuco Assets Creator"
    bl_idname = "OBJECT_PT_cuco_assets_creator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cuco Assets Creator"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.cuco_assets_creator")

def register():
    bpy.utils.register_class(ConvertToGTAVAsset)
    bpy.utils.register_class(CucoAssetsCreatorPanel)

def unregister():
    bpy.utils.unregister_class(ConvertToGTAVAsset)
    bpy.utils.unregister_class(CucoAssetsCreatorPanel)

if __name__ == "__main__":
    register()