from nion.utils import Registry

my_insts = Registry.get_components_by_type("stem_controller")
for my_inst in list(my_insts):
    print(my_inst.instrument_id)
