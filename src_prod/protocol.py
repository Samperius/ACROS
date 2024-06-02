from opentrons import protocol_api


metadata = {'apiLevel': '2.13', 'protocolName': 'Batch 1 reactions 1-16', 'description': '...', 'author': 'Samuli'}


class OT:
   def __init__(self, pipette, tip_rack):
      self.pipette = pipette
      self.tip_rack = tip_rack
   def transfer(self, volume, source, destination, blow_out=True, blowout_location='destination well', air_gap=0, new_tip = True, drop_old_tip = True):
      pipette = self.pipette
      tip_rack = self.tip_rack
      if new_tip:
         pipette.pick_up_tip(tip_rack)
      left_over = volume
      max_pipetting_volume = 900
      while left_over > max_pipetting_volume-air_gap:
         if left_over < (max_pipetting_volume*2) and left_over > max_pipetting_volume and left_over-max_pipetting_volume<100:
            pipetting_volume = left_over/2
         else:
            pipetting_volume = max_pipetting_volume
         pipette.aspirate(pipetting_volume-air_gap , source)
         if air_gap > 0:
            pipette.air_gap(air_gap)
         pipette.dispense(pipetting_volume, destination)
         if blow_out:
            pipette.blow_out(destination)
         left_over -= pipetting_volume-air_gap
      if left_over > 0:
         pipette.aspirate(left_over, source)
         if air_gap > 0:
            pipette.air_gap(air_gap)
         pipette.dispense(left_over+air_gap, destination)
         if blow_out:
            pipette.blow_out(destination)
      if drop_old_tip:
         pipette.drop_tip()
      return pipette

def run(protocol: protocol_api.ProtocolContext):
   tip_rack = protocol.load_labware('opentrons_96_tiprack_1000ul', 1)
   pipette = protocol.load_instrument('p1000_single', 'right', tip_racks=[tip_rack])
   ot = OT(pipette, tip_rack)
   normal_rack_1 = protocol.load_labware('chemspeed_24_tuberack_8000ul', 2)
   normal_rack_2 = protocol.load_labware('chemspeed_24_tuberack_8000ul', 2)
   hs_mod = protocol.load_module(module_name='heaterShakerModuleV1', location=7)
   heater_shaker_rack_1 = hs_mod.load_labware(name='chemspeed_24_tuberack_8000ul', label='chemspeed_24_tuberack_8000ul')
   hs_mod = protocol.load_module(module_name='heaterShakerModuleV1', location=7)
   heater_shaker_rack_2 = hs_mod.load_labware(name='chemspeed_24_tuberack_8000ul', label='chemspeed_24_tuberack_8000ul')
   analysis_rack_1 = protocol.load_labware('chemspeed_24_tuberack_8000ul', 6)
   analysis_rack_2 = protocol.load_labware('chemspeed_24_tuberack_8000ul', 6)
   solvent_rack_1 = protocol.load_labware('chemspeed_24_tuberack_8000ul', 3)
   solvent_rack_2 = protocol.load_labware('chemspeed_24_tuberack_8000ul', 3)
   hs_mod.close_labware_latch()   #add new ms
   #transfering solvent
   ot.transfer(volume=9707.137893028197,source=solvent_rack_2['B1'],destination=heater_shaker_rack_1['C1'].top(), drop_old_tip=False, new_tip=True, blow_out=True, air_gap=100)
   #transfering solvent
   ot.transfer(volume=9707.137893028197,source=solvent_rack_2['B1'],destination=heater_shaker_rack_1['C3'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering solvent
   ot.transfer(volume=9707.137893028197,source=solvent_rack_2['B1'],destination=heater_shaker_rack_1['C5'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering solvent
   ot.transfer(volume=9707.137893028197,source=solvent_rack_2['B1'],destination=heater_shaker_rack_1['D1'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering solvent
   ot.transfer(volume=9707.137893028197,source=solvent_rack_2['B1'],destination=heater_shaker_rack_1['D3'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering solvent
   ot.transfer(volume=9707.137893028197,source=solvent_rack_2['B1'],destination=heater_shaker_rack_1['D5'].top(), drop_old_tip=True, new_tip=False, blow_out=True, air_gap=100)
   #transfering reactant 1
   ot.transfer(volume=169.8189415041783,source=normal_rack_1['C6'],destination=heater_shaker_rack_1['C1'].top(), drop_old_tip=False, new_tip=True, blow_out=True, air_gap=100)
   #transfering reactant 1
   ot.transfer(volume=169.8189415041783,source=normal_rack_1['C6'],destination=heater_shaker_rack_1['C3'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering reactant 1
   ot.transfer(volume=169.8189415041783,source=normal_rack_1['C6'],destination=heater_shaker_rack_1['C5'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering reactant 1
   ot.transfer(volume=169.8189415041783,source=normal_rack_1['C6'],destination=heater_shaker_rack_1['D1'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering reactant 1
   ot.transfer(volume=169.8189415041783,source=normal_rack_1['C6'],destination=heater_shaker_rack_1['D3'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering reactant 1
   ot.transfer(volume=169.8189415041783,source=normal_rack_1['C6'],destination=heater_shaker_rack_1['D5'].top(), drop_old_tip=True, new_tip=False, blow_out=True, air_gap=100)
   #transfering reactant 2
   ot.transfer(volume=123.04316546762591,source=normal_rack_1['D1'],destination=heater_shaker_rack_1['C1'].top(), drop_old_tip=False, new_tip=True, blow_out=True, air_gap=100)
   #transfering reactant 2
   ot.transfer(volume=123.04316546762591,source=normal_rack_1['D1'],destination=heater_shaker_rack_1['C3'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering reactant 2
   ot.transfer(volume=123.04316546762591,source=normal_rack_1['D1'],destination=heater_shaker_rack_1['C5'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering reactant 2
   ot.transfer(volume=123.04316546762591,source=normal_rack_1['D1'],destination=heater_shaker_rack_1['D1'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering reactant 2
   ot.transfer(volume=123.04316546762591,source=normal_rack_1['D1'],destination=heater_shaker_rack_1['D3'].top(), drop_old_tip=False, new_tip=False, blow_out=True, air_gap=100)
   #transfering reactant 2
   ot.transfer(volume=123.04316546762591,source=normal_rack_1['D1'],destination=heater_shaker_rack_1['D5'].top(), drop_old_tip=True, new_tip=False, blow_out=True, air_gap=100)
   hs_mod.set_target_temperature(120.0)
   protocol.delay(minutes=0.5)
   hs_mod.set_and_wait_for_shake_speed(600.0)
   hs_mod.wait_for_temperature()
   protocol.delay(minutes=15.0604693385327)
   hs_mod.deactivate_shaker()
   hs_mod.deactivate_heater()
   ot.transfer(volume=4900.0,source=solvent_rack_2['A1'],destination=normal_rack_1['B5'].top(), blow_out=True, air_gap=100)
   pipette.pick_up_tip(tip_rack)
   pipette.drop_tip()
   ot.transfer(volume=100.0,source=normal_rack_1['C5'],destination=normal_rack_1['B5'].top(), blow_out=True, air_gap=100)
   hs_mod.set_target_temperature(120.0)
   protocol.delay(minutes=0.5)
   hs_mod.set_and_wait_for_shake_speed(600.0)
   hs_mod.wait_for_temperature()
   protocol.delay(minutes=-11.0604693385327)
   hs_mod.deactivate_shaker()
   hs_mod.deactivate_heater()
   ot.transfer(volume=4900.0,source=solvent_rack_2['A1'],destination=normal_rack_1['B6'].top(), blow_out=True, air_gap=100)
   pipette.pick_up_tip(tip_rack)
   pipette.drop_tip()
   ot.transfer(volume=100.0,source=normal_rack_1['C5'],destination=normal_rack_1['B6'].top(), blow_out=True, air_gap=100)
   hs_mod.set_target_temperature(120.0)
   protocol.delay(minutes=0.5)
   hs_mod.set_and_wait_for_shake_speed(600.0)
   hs_mod.wait_for_temperature()
   protocol.delay(minutes=18.9394514699475)
   hs_mod.deactivate_shaker()
   hs_mod.deactivate_heater()
   ot.transfer(volume=4900.0,source=solvent_rack_2['A1'],destination=normal_rack_1['C1'].top(), blow_out=True, air_gap=100)
   pipette.pick_up_tip(tip_rack)
   pipette.drop_tip()
   ot.transfer(volume=100.0,source=normal_rack_1['C5'],destination=normal_rack_1['C1'].top(), blow_out=True, air_gap=100)
   hs_mod.set_target_temperature(120.0)
   protocol.delay(minutes=0.5)
   hs_mod.set_and_wait_for_shake_speed(600.0)
   hs_mod.wait_for_temperature()
   protocol.delay(minutes=-26.1163122398455)
   hs_mod.deactivate_shaker()
   hs_mod.deactivate_heater()
   ot.transfer(volume=4900.0,source=solvent_rack_2['A1'],destination=normal_rack_1['C2'].top(), blow_out=True, air_gap=100)
   pipette.pick_up_tip(tip_rack)
   pipette.drop_tip()
   ot.transfer(volume=100.0,source=normal_rack_1['C5'],destination=normal_rack_1['C2'].top(), blow_out=True, air_gap=100)
   hs_mod.set_target_temperature(120.0)
   protocol.delay(minutes=0.5)
   hs_mod.set_and_wait_for_shake_speed(600.0)
   hs_mod.wait_for_temperature()
   protocol.delay(minutes=-80.41074403702419)
   hs_mod.deactivate_shaker()
   hs_mod.deactivate_heater()
   ot.transfer(volume=4900.0,source=solvent_rack_2['A1'],destination=normal_rack_1['C3'].top(), blow_out=True, air_gap=100)
   pipette.pick_up_tip(tip_rack)
   pipette.drop_tip()
   ot.transfer(volume=100.0,source=normal_rack_1['C5'],destination=normal_rack_1['C3'].top(), blow_out=True, air_gap=100)
   hs_mod.set_target_temperature(120.0)
   protocol.delay(minutes=0.5)
   hs_mod.set_and_wait_for_shake_speed(600.0)
   hs_mod.wait_for_temperature()
   protocol.delay(minutes=-71.5981920713364)
   hs_mod.deactivate_shaker()
   hs_mod.deactivate_heater()
   ot.transfer(volume=4900.0,source=solvent_rack_2['A1'],destination=normal_rack_1['C4'].top(), blow_out=True, air_gap=100)
   pipette.pick_up_tip(tip_rack)
   pipette.drop_tip()
   ot.transfer(volume=100.0,source=normal_rack_1['C5'],destination=normal_rack_1['C4'].top(), blow_out=True, air_gap=100)