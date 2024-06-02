import os
import numpy as np
import pandas as pd
from OT_entity_prod import Rack, Rack_capacity_handler

class OT_service:
    def __init__(self, settings_path,data_dir) -> None:
        self.data_dir = data_dir
        #self.ot = OpenTrons(solutions=None, combined_solutions=None)
        self._initialize(settings_path)
        self.dilution_factors = []


    def _initialize(self, settings_path):
        ot_settings = pd.read_excel(settings_path)
        self.read_settings(ot_settings)
        self.solutions = pd.read_excel(os.path.join(self.data_dir, self.solutions_file_name))
        self.create_ms_solution()
        self.read_solutions(self.solutions)
        self.check_time_temperature_and_shaker()
        self.check_reactions()

    def read_settings(self, settings_df):                
        self.blowout = settings_df[settings_df['setting'] == 'blowout']['value'].values[0]
        self.air_gap = settings_df[settings_df['setting'] == 'air_gap']['value'].values[0]
        self.shaker_rounds_per_minute = settings_df[settings_df['setting'] == 'shaker rounds per minute']['value'].values[0]
        self.heater_shaker_offset = settings_df[settings_df['setting'] == 'heater shaker offset']['value'].values[0]
        self.additional_offset = settings_df[settings_df['setting'] == 'additional offset from bottom']['value'].values[0]
        self.neg_offset = settings_df[settings_df['setting'] == 'Negative offset from top']['value'].values[0]
        self.work_pause = settings_df[settings_df['setting'] == 'work pause']['value'].values[0]
        self.tip_rack = settings_df[settings_df['setting'] == 'tip rack']['value'].values[0]
        self.tip_rack_slot = settings_df[settings_df['setting'] == 'tip rack slot']['value'].values[0]
        self.free_space = settings_df[settings_df['setting'] == 'free space']['value'].values[0]
        self.ms_volume_safety_factor = settings_df[settings_df['setting'] == 'ms volume safety margin']['value'].values[0]
        self.api_level = settings_df[settings_df['setting'] == 'api level']['value'].values[0]
        self.protocol_name = settings_df[settings_df['setting'] == 'protocol name']['value'].values[0]
        self.author = settings_df[settings_df['setting'] == 'author']['value'].values[0]
        self.analysis = settings_df[settings_df['setting'] == 'analysis']['value'].values[0]
        if self.analysis == 'yes':
            self.analysis = True
        self.adapter_offset = settings_df[settings_df['setting'] == 'adapter offset']['value'].values[0]
        self.ms = settings_df[settings_df['setting'] == 'mother solution']['value'].values[0]
        if self.ms == 'yes':
            self.ms = True
        self.shaker = settings_df[settings_df['setting'] == 'shaker']['value'].values[0]
        if self.shaker == 'yes':
            self.shaker = True
        self.mix_before_sampling_from_heater_shaker = settings_df[settings_df['setting'] == 'mix before sampling from heater shaker']['value'].values[0]
        if self.mix_before_sampling_from_heater_shaker== 'yes':
            self.mix_before_sampling_from_heater_shaker = True
        self.solutions_file_name = settings_df[settings_df['setting'] == 'solutions file name']['value'].values[0]
        self.internal_standard = settings_df[settings_df['setting'] == 'internal standard']['value'].values[0]
        self.capacity_handler = Rack_capacity_handler()
        #normal racks
        self.read_racks(settings_df, 'rack')     
        #heater shaker racks
        self.read_racks(settings_df, 'heater-shaker rack')
        #analysis racks
        self.read_racks(settings_df, 'analysis rack')
        #solvent racks
        self.read_racks(settings_df, 'solvent rack')
    
    def read_solutions(self, solutions_df):
        ms_solutions_df = pd.read_excel(os.path.join(self.data_dir, 'ms_solutions.xlsx'))
        
        #solutions_df['component'] = solutions_df['component'].apply(lambda x: x + " ms" if 'reactant' in x else x)
        if self.ms:
            solutions_df = pd.concat([solutions_df, ms_solutions_df], ignore_index=True)

        sums_of_volumes = solutions_df.groupby('component')['volume'].sum()
        is_filtered_solutions_df = solutions_df[solutions_df['component'] != 'internal standard']
        is_filtered_solutions_df = is_filtered_solutions_df[is_filtered_solutions_df['component'] != 'product']
        is_filtered_solutions_df = is_filtered_solutions_df[is_filtered_solutions_df['component'] != 'analysis solvent']
        is_filtered_solutions_df = is_filtered_solutions_df[is_filtered_solutions_df['component'] != 'reaction solution in analysis sample']
        #remove all analysis samples
        for i in range(20):
            is_filtered_solutions_df = is_filtered_solutions_df[is_filtered_solutions_df['component'] != f'analysis sample {i+1}']

        sum_of_reactions = is_filtered_solutions_df.groupby('experiment name')['volume'].sum()
        self.reactions = {}
        previous_reaction = solutions_df['experiment name'][0]
        components = {}

        for i, row in solutions_df.iterrows():
            if row['experiment name'] != previous_reaction:
                self.reactions[row['experiment name']] = components
                components = {}
            components[row['component']] = {'name':row['name'],'volume': row['volume'], 'experiment': row['experiment name'], 'amount': row['amount'], 'ms-factor': row['ms-factor'],'temperature': row['temperature'], 'time': row['time'], 'shaker speed': row['shaker speed'], 'mix order': row['mix order']}
            previous_reaction = row['experiment name']

        for component, volume  in sums_of_volumes.items():
                component_name = component
                print('component name', component_name)
                self.capacity_handler.allocate_rack_for_component(component_name, volume)
        
        print(sum_of_reactions)
        for reaction, volume in sum_of_reactions.items():
                self.capacity_handler.allocate_rack_for_component(reaction, volume)
        
        self.sum_of_reaction_volumes = sum_of_reactions
        print('capacity handler places when initialized', self.capacity_handler.rack_place)

    def read_racks(self, settings_df, rack_type):
        for i, rack in enumerate(settings_df[settings_df['setting'] == f'{rack_type}']['value'].values):
            rack_name = rack
            rack_slot = settings_df[settings_df['setting'] == f'{rack_type} slot']['value'].values[i]
            rack_columns = settings_df[settings_df['setting'] == f'{rack_type} columns']['value'].values[i]
            rack_rows = settings_df[settings_df['setting'] == f'{rack_type} rows']['value'].values[i]
            rack_bottle_volume = settings_df[settings_df['setting'] == f'{rack_type} bottle volume']['value'].values[i]
            rack = Rack(name=rack_name, slot=rack_slot, columns=rack_columns, rows=rack_rows, bottle_volume=rack_bottle_volume, free_space=self.free_space)
            if rack_type == 'rack':
                self.capacity_handler.normal_racks.append(rack)
            elif rack_type == 'heater-shaker rack':
                self.capacity_handler.heater_shaker_racks.append(rack)
            elif rack_type == 'analysis rack':
                self.capacity_handler.analysis_racks.append(rack)
            elif rack_type == 'solvent rack':
                self.capacity_handler.solvent_racks.append(rack)

    def check_mother_solution(self):
        for i, row in self.solutions_df.iterrows():
            if row['ms-factor'] > 1:
                return True
        return False
    
    def calculate_total_volumes_per_component(self):
        components = {}
        for i, row in self.solutions_df.iterrows():
            if row['component'] not in components:
                components[row['component']] = row['volume']
            else:
                components[row['component']] += row['volume']
        return components
    
    def create_meta_data():
        pass

    def check_reactions(self):
        self.reactions = []
        for i, row in self.solutions.iterrows():
            if row['experiment name'] not in self.reactions:
                self.reactions.append(row['experiment name'])
        return self.reactions
    
    def check_components(self):
        components = []
        for i, row in self.solutions_df.iterrows():
            if row['component'] not in components and row['component'] not in [None, '', 'reaction']:
                components.append(row['component'])
        return components
    
    def check_time_temperature_and_shaker(self):
        self.times = []
        self.temperatures = []
        self.shaker_speeds = []
        self.fixed_time = True
        self.fixed_temperature = True
        self.fixed_shaker_speed = True
        for i, row in self.solutions.iterrows():
            if np.isnan(row['time']) == False:
                if row['time'] not in self.times and self.times != []:
                    self.times.append(row['time'])
                    self.fixed_time = False
                else:
                    self.times.append(row['time'])

            if np.isnan(row['temperature']) == False:
                if row['temperature'] not in self.temperatures and self.temperatures != []:
                    self.temperatures.append(row['temperature'])
                    self.fixed_temperature = False
                elif row['temperature'] not in self.temperatures and self.temperatures == []:
                    self.temperatures.append(row['temperature'])

            if np.isnan(row['shaker speed']) == False:
                if row['shaker speed'] not in self.shaker_speeds and self.shaker_speeds != []:
                    self.shaker_speeds.append(row['shaker speed'])
                    self.fixed_shaker_speed = False
                elif row['shaker speed'] not in self.shaker_speeds and self.shaker_speeds == []:
                    self.shaker_speeds.append(row['shaker speed'])
        

    def initialize_protocol(self):
        protocol = ["from opentrons import protocol_api",
"\n",                         
f"metadata = {{'apiLevel': '2.13', 'protocolName': '{self.protocol_name}', 'description': '...', 'author': '{self.author}'}}",
"\n",
f"class OT:",
f"   def __init__(self, pipette, tip_rack):",
f"      self.pipette = pipette",
f"      self.tip_rack = tip_rack",
f"   def transfer(self, volume, source, destination, blow_out=True, blowout_location='destination well', air_gap=0, new_tip = True, drop_old_tip = True):",
f"      pipette = self.pipette",
f"      tip_rack = self.tip_rack",
f"      if new_tip:",
f"         pipette.pick_up_tip(tip_rack)",
f"      left_over = volume",
f"      max_pipetting_volume = 900",
f"      while left_over > max_pipetting_volume-air_gap:",
f"         if left_over < (max_pipetting_volume*2) and left_over > max_pipetting_volume and left_over-max_pipetting_volume<100:",
f"            pipetting_volume = left_over/2",
f"         else:",
f"            pipetting_volume = max_pipetting_volume",
f"         pipette.aspirate(pipetting_volume-air_gap , source)",
f"         if air_gap > 0:",
f"            pipette.air_gap(air_gap)",
f"         pipette.dispense(pipetting_volume, destination)",
f"         if blow_out:",
f"            pipette.blow_out(destination)",
f"         left_over -= pipetting_volume-air_gap",
f"      if left_over > 0:",
f"         pipette.aspirate(left_over, source)",
F"         if air_gap > 0:",
f"            pipette.air_gap(air_gap)",
f"         pipette.dispense(left_over+air_gap, destination)",
f"         if blow_out:",
f"            pipette.blow_out(destination)",
f"      if drop_old_tip:",
f"         pipette.drop_tip()",
f"      return pipette"
"\n",
"def run(protocol: protocol_api.ProtocolContext):",
f"   tip_rack = protocol.load_labware('{self.tip_rack}', {int(self.tip_rack_slot)})",
f"   pipette = protocol.load_instrument('p1000_single', 'right', tip_racks=[tip_rack])",
"   ot = OT(pipette, tip_rack)"]
        racks = []
        for i, rack in enumerate(self.capacity_handler.normal_racks):
             racks.append(f"   normal_rack_{i+1} = protocol.load_labware('{rack.name}', {rack.slot})")
        for i, rack in enumerate(self.capacity_handler.heater_shaker_racks):
                racks.append("   hs_mod = protocol.load_module(module_name='heaterShakerModuleV1', location=7)")
                racks.append(f"   heater_shaker_rack_{i+1} = hs_mod.load_labware(name='{rack.name}', label='{rack.name}')")
        if self.capacity_handler.analysis_racks != []:
            for i, rack in enumerate(self.capacity_handler.analysis_racks):
                racks.append(f"   analysis_rack_{i+1} = protocol.load_labware('{rack.name}', {rack.slot})")
        if self.capacity_handler.solvent_racks != []:
            for i, rack in enumerate(self.capacity_handler.solvent_racks):
                racks.append(f"   solvent_rack_{i+1} = protocol.load_labware('{rack.name}', {rack.slot})")
        racks.append("   hs_mod.close_labware_latch()   #add new ms\n")

        with open('protocol.py', 'w') as f:
            f.write('\n'.join(protocol + racks))
        

    def calculate_ms_needed(self):
        volumes = {}
        for i, row in self.solutions.iterrows():
            if row['ms-factor'] > 1:
                if row['component'] in volumes:
                    volumes[row['component']][0]+=row['volume']
                else:
                    volumes[row['component']] = [row['volume'], row['ms-factor']]
                
        return volumes

    def create_ms_solution(self):
        self.ms_solution = {
            'ms': [], #the material that is diluted
            'component': [],
            'volume': [],
            'mix order': [],
        }
        volumes = self.calculate_ms_needed()

        for component in volumes.keys():
            #reactant
            self.ms_solution['ms'].append(component)
            self.ms_solution['component'].append(component.strip('ms'))
            self.ms_solution['volume'].append(volumes[component][0]*(1/volumes[component][1])*(1+self.ms_volume_safety_factor))
            self.ms_solution['mix order'].append(1+int(component.split()[1]))
            #solvent
            self.ms_solution['ms'].append(component)
            self.ms_solution['component'].append('solvent')
            self.ms_solution['volume'].append(volumes[component][0]*(1-(1/volumes[component][1]))*(1+self.ms_volume_safety_factor))
            self.ms_solution['mix order'].append(1)
              
                
        df = pd.DataFrame(self.ms_solution)
        df.to_excel(os.path.join(self.data_dir, 'ms_solutions.xlsx'), index=False)

    def transfer_ms_solution(self):
        self.ms_solution = pd.read_excel(os.path.join(self.data_dir, 'ms_solutions.xlsx'))
        self.ot_functions = []
        dispense_pos = f".top()"
        #iterate mixorders
        for j in range(1, len(self.ms_solution)):
            for r_i, row in self.ms_solution.iterrows():
                if row['mix order'] == j:
                    source, position_indexes = self.capacity_handler.find_source(row['component'], row['volume'])
                    destination = self.capacity_handler.find_destination(row['ms'])
                    leftover = row['volume']
                    i = 0
                    while leftover > 0:
                        if source['volumes'][i] >= leftover:
                            source_place = self.row_column_index_to_OT_coordinates(source['rows'][i], source['columns'][i])
                            destination_place = self.row_column_index_to_OT_coordinates(destination['rows'][i], destination['columns'][i])
                            
                            v=leftover * 1000
                            s = f"{source['racks'][i]}['{source_place}']"
                            d=f"{destination['racks'][i]}['{destination_place}']{dispense_pos}"
                            leftover = 0
                        else:
                            v = int(source['volumes'][i])*1000
                            s=f"{source['racks'][i]}['{source_place}']"
                            d =f"{destination['racks'][i]}['{destination_place}']{dispense_pos}"
                            leftover -= source['volumes'][i]

                        self.ot_functions.append(f"   ot.transfer(volume={v},source={s},destination={d})")
                        i += 1
        
    def transfer_component(self, component, reaction):
        dispense_pos = f".top()"
        dispense_index = 0
        count_components = 0
        component_index = 0
        if reaction:
            solutions = self.solutions[self.solutions['experiment name'] == reaction]
        else:
            solutions = self.solutions
        for i, row in solutions.iterrows(): 
            if row['component'] == component:
                count_components += 1
        for j, row in solutions.iterrows():
            if 'reactant' in component:
                print('row', row['component'], 'component', component, 'count components', count_components, 'component index', component_index)
            if component == row['component']:
                print('pass if')
                source, position_indexes = self.capacity_handler.find_source(row['component'], row['volume'])
                destination = self.capacity_handler.find_destination(row['experiment name'])
                leftover = row['volume']
                k = 0
                
                while leftover-0.01 > 0:
                    source_place = self.row_column_index_to_OT_coordinates(source['rows'][k], source['columns'][k])
                    destination_place = self.row_column_index_to_OT_coordinates(destination['rows'][0], destination['columns'][0])

                    if source['volumes'][k]+0.01 >= leftover:
                        v=leftover * 1000
                        s = f"{source['racks'][0]}['{source_place}']"
                        d=f"{destination['racks'][0]}['{destination_place}']{dispense_pos}"
                        leftover = 0
                    
                    else:
                        v = (source['volumes'][k])*1000
                        s=f"{source['racks'][0]}['{source_place}']"
                        d =f"{destination['racks'][0]}['{destination_place}']{dispense_pos}"
                        leftover -= source['volumes'][k]
                    print('k', k, 'count components', count_components, 'component index', component_index)

                    if len(source['rows']) == 1 and count_components == 1 and v>10:
                        print('only one component')
                        #first and last
                        self.ot_functions.append(f"   #transfering {component}")
                        self.ot_functions.append(f"   ot.transfer(volume={v},source={s},destination={d}, drop_old_tip=True, new_tip=True, blow_out={bool(self.blowout)}, air_gap={self.air_gap})")
                        #first and not last
                    elif dispense_index == 0 and (len(source['rows'])>1 or count_components > component_index+1) and v>10:
                        print('first not last')
                        self.ot_functions.append(f"   #transfering {component}")
                        self.ot_functions.append(f"   ot.transfer(volume={v},source={s},destination={d}, drop_old_tip=False, new_tip=True, blow_out={bool(self.blowout)}, air_gap={self.air_gap})")
                        #not first or last
                    elif dispense_index > 0 and dispense_index < len(source['rows'])-1 and v>10:
                        print('not first not last')
                        self.ot_functions.append(f"   #transfering {component}")
                        self.ot_functions.append(f"   ot.transfer(volume={v},source={s},destination={d}, drop_old_tip=False, new_tip=False, blow_out={bool(self.blowout)}, air_gap={self.air_gap})")
                        
                    elif v>10 and dispense_index > 0 and leftover < row['volume']-0.01 and component_index<count_components-1:
                        print('not first not last?')
                        self.ot_functions.append(f"   #transfering {component}")
                        self.ot_functions.append(f"   ot.transfer(volume={v},source={s},destination={d}, drop_old_tip=False, new_tip=False, blow_out={bool(self.blowout)}, air_gap={self.air_gap})")
                    #last
                    elif v>10:
                        print('last')
                        self.ot_functions.append(f"   #transfering {component}")
                        self.ot_functions.append(f"   ot.transfer(volume={v},source={s},destination={d}, drop_old_tip=True, new_tip=False, blow_out={bool(self.blowout)}, air_gap={self.air_gap})")
                    dispense_index += 1
                    k += 1
                component_index += 1
                
    def start_stop_heater_shaker(self, reaction_index):
        elapsed_time = 0
        number_of_work_pauses = 0
        if self.fixed_time and self.fixed_temperature and self.temperatures and self.shaker_speeds:
            self.ot_functions.append(f"   hs_mod.set_target_temperature({self.temperatures[0]})")
            if self.shaker:
                self.ot_functions.append(f"   protocol.delay(minutes={self.work_pause})")
                elapsed_time += self.work_pause
                self.ot_functions.append(f"   hs_mod.set_and_wait_for_shake_speed({self.shaker_speeds[0]})")
            self.ot_functions.append(f"   hs_mod.wait_for_temperature()")
            self.ot_functions.append(f"   protocol.delay(minutes={self.times[0]-elapsed_time})")
            if self.shaker:
                self.ot_functions.append(f"   hs_mod.deactivate_shaker()")
            self.ot_functions.append(f"   hs_mod.deactivate_heater()")
        elif self.fixed_time and not self.fixed_temperature and self.temperatures and self.shaker_speeds:
            if self.shaker:
                self.ot_functions.append(f"   hs_mod.set_and_wait_for_shake_speed({self.shaker_speeds[0]})")
            self.ot_functions.append(f"   hs_mod.set_and_wait_for_target_temperature({self.temperatures[reaction_index]})")
            self.ot_functions.append(f"   protocol.delay(minutes={self.times[0]})")
            if self.shaker:
                self.ot_functions.append(f"   hs_mod.deactivate_shaker()")
            self.ot_functions.append(f"   hs_mod.deactivate_heater()")
        elif not self.fixed_time and self.fixed_temperature and self.temperatures and self.shaker_speeds:
            elapsed_time = 0
            number_of_work_pauses = 0
            for i in range(reaction_index):
                elapsed_time += self.times[i]
            
            
            self.ot_functions.append(f"   hs_mod.set_target_temperature({self.temperatures[0]})")
            if self.work_pause:
                number_of_work_pauses += 1
                self.ot_functions.append(f"   protocol.delay(minutes={self.work_pause})")
            if self.shaker:
                self.ot_functions.append(f"   hs_mod.set_and_wait_for_shake_speed({self.shaker_speeds[0]})")
            self.ot_functions.append(f"   hs_mod.wait_for_temperature()")
            time = self.times[reaction_index] - elapsed_time - self.work_pause*(number_of_work_pauses)
            elapsed_time += time
            self.ot_functions.append(f"   protocol.delay(minutes={time})")
            if self.shaker:
                self.ot_functions.append(f"   hs_mod.deactivate_shaker()")
            self.ot_functions.append(f"   hs_mod.deactivate_heater()")
        elif not self.fixed_time and not self.fixed_temperature and self.temperatures and self.shaker_speeds:
            self.ot_functions.append(f"   hs_mod.set_target_temperature({self.temperatures[reaction_index]})")
            if self.shaker:
                self.ot_functions.append(f"   hs_mod.set_and_wait_for_shake_speed({self.shaker_speeds[0]})")
            self.ot_functions.append(f"   hs_mod.wait_for_temperature()")
            self.ot_functions.append(f"   protocol.delay(minutes={self.times[reaction_index]})")
            if self.shaker:
                self.ot_functions.append(f"   hs_mod.deactivate_shaker()")
            self.ot_functions.append(f"   hs_mod.deactivate_heater()")
    
    def return_number_of_reactants(self):
        reactants = []
        for i, row in self.solutions.iterrows():
            if type(row['component']) != str:
                continue
            if 'reactant' in row['component'] and row['component'] not in reactants:
                reactants.append(row['component'])
        
        return len(reactants)
                
    def transfer_reaction(self, reaction):
        self.transfer_component('solvent',reaction)
        self.transfer_component('base',reaction)
        self.transfer_component('acid',reaction)
        for i in range(self.return_number_of_reactants()):
            self.transfer_component(f'reactant {i+1}',reaction)
        self.transfer_component('liquid catalyst',reaction)

    def row_column_index_to_OT_coordinates(self, row, column):
        rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        return rows[row] + str(column+1)

    def modify_source_and_destination(self, location_dict, position_indexes=[0]):
        if type(location_dict) != dict:
            location_dict = location_dict[0]
        if len(location_dict['racks']) == 1:
            i = 0
            position = self.row_column_index_to_OT_coordinates(location_dict['rows'][i], location_dict['columns'][i])
            rack_and_position = f"{location_dict['racks'][0]}['{position}']"

        else:
            rack_and_position = []
            for i in range(position_indexes):
                position = self.row_column_index_to_OT_coordinates(location_dict['rows'][i], location_dict['columns'][i])
                rack_and_position.append(f"{location_dict['racks'][0]}['{position}']")
            
        return rack_and_position

    def mix_analysis_sample(self, reaction_i, reaction):
        #reaction_solution_in_analysis_sample_volume = self.solutions[self.solutions['component'] == 'reaction solution in analysis sample']['volume'].values[0]
        analysis_solvent_volume = self.solutions[self.solutions['component'] == 'analysis solvent']['volume'].values[0]
        #reaction_solution_source = self.modify_source_and_destination(self.capacity_handler.find_source(reaction,reaction_solution_in_analysis_sample_volume))
        analysis_solvent_source = self.modify_source_and_destination(self.capacity_handler.find_source('analysis solvent',analysis_solvent_volume))
        internal_standard_volume = self.solutions[self.solutions['component'] == 'internal standard']['volume'].values[0]
        internal_standard_source = self.modify_source_and_destination(self.capacity_handler.find_source('internal standard',internal_standard_volume))

        #if type(reaction_solution_source)== list or type(analysis_solvent_source) == list:
        #    raise Exception('More than one rack for analysis sample or analysis solvent. Not implemented yet')
        destination = self.capacity_handler.find_destination(f"analysis sample {reaction_i+1}")
        destination = self.modify_source_and_destination(destination)
        dispense_pos = f".top()"
        aspirate_pos = f".bottom({self.adapter_offset})"
        
        self.ot_functions.append(f"   ot.transfer(volume={analysis_solvent_volume*1000},source={analysis_solvent_source},destination={destination+dispense_pos}, blow_out={bool(self.blowout)}, air_gap={self.air_gap})")
        if self.mix_before_sampling_from_heater_shaker:
            self.ot_functions.append(f"   pipette.pick_up_tip(tip_rack)")
        #   self.ot_functions.append(f"   pipette.mix(3, 300, {reaction_solution_source+aspirate_pos})")
            self.ot_functions.append(f"   pipette.drop_tip()")
        #internal standard
        if self.internal_standard:
            self.ot_functions.append(f"   ot.transfer(volume={internal_standard_volume*1000},source={internal_standard_source},destination={destination+dispense_pos}, blow_out={bool(self.blowout)}, air_gap={self.air_gap})")
        #self.ot_functions.append(f"   ot.transfer(volume={reaction_solution_in_analysis_sample_volume*1000},source={reaction_solution_source+aspirate_pos},destination={destination+dispense_pos}, blow_out={bool(self.blowout)}, air_gap={self.air_gap})")

    def create_rackmap(self):
        items_in_normal_racks = {
            'rack_slot':[],
            'rack':[],
            'material':[],
            'rack position':[],
            'volume':[],
        }
        for material in self.capacity_handler.rack_place.keys():
            material_dict = self.capacity_handler.rack_place[material]
            rack_name = material_dict['racks'][0].split('_')[0]
            print('rack name', rack_name)
            rack_i = int(rack_name.split('_')[-1])
            
            if 'normal rack' in rack_name:
                rack_slot = self.capacity_handler.normal_racks[rack_i-1].slot
                items_in_normal_racks['rack'].append(rack_name)
                items_in_normal_racks['rack_slot'].append(rack_slot)
                items_in_normal_racks['material'].append(material)
                items_in_normal_racks['rack position'].append(self.row_column_index_to_OT_coordinates(material_dict['rows'][0], material_dict['columns'][0]))
                items_in_normal_racks['volume'].append(material_dict['volumes'][0])
    
                #save to excel
        df = pd.DataFrame(items_in_normal_racks)
        df.to_excel(os.path.join(self.data_dir, 'rackmap.xlsx'), index=False)

    def create_main_logic(self):
        self.initialize_protocol()
        #self.create_meta_information()
        if self.ms:
            self.transfer_ms_solution()
        else:
            self.ot_functions = []
        #self.create_metadata(self, api_level, name)
        print('fixed time', self.fixed_time, 'fixed temperature', self.fixed_temperature)
        if self.fixed_time and self.fixed_temperature:
            print('fixed time and temperature')
            self.transfer_component('solvent', None)
            self.transfer_component('base', None)
            self.transfer_component('acid', None)
            for i in range(self.return_number_of_reactants()):
                print('mixing reactant ', i+1)
                if self.ms:
                    self.transfer_component(f'reactant {i+1} ms', None)
                else:
                    self.transfer_component(f'reactant {i+1}', None)
            self.transfer_component('liquid catalyst', None)
            self.start_stop_heater_shaker(self.times)
            if self.analysis:
                for i, reaction in enumerate(self.reactions):
                    self.mix_analysis_sample(i, reaction)
        
        if self.fixed_time and not self.fixed_temperature:
            print('fixed time and variable temperature')
            for i, reaction in enumerate(self.reactions):
                self.transfer_reaction(reaction)
                self.start_stop_heater_shaker(i)
                if self.analysis:
                    self.mix_analysis_sample(reaction)

        if not self.fixed_time and self.fixed_temperature:
            print('fixed temperature and variable time')
            print('solvent')
            self.transfer_component('solvent', None)
            print('base')
            self.transfer_component('base', None)
            print('acid')
            self.transfer_component('acid', None)
            print('transfer reactants')
            for i in range(self.return_number_of_reactants()):
                print(f'reactant {i+1}')
                self.transfer_component(f'reactant {i+1}', None)
            self.transfer_component('liquid catalyst', None)

            for i, reaction in enumerate(self.reactions):
                print('heat and mix reaction', i+1)
                self.start_stop_heater_shaker(i)
                if self.analysis:
                    self.mix_analysis_sample(i, reaction)
        
        with open('protocol.py', 'a') as f:
                f.write('\n'.join(self.ot_functions))
        
        


