import numpy as np
import copy
class Rack:
    def __init__(self, name, slot, columns, rows, bottle_volume, free_space):
        self.name = name
        self.slot = slot
        self.columns = int(columns)
        self.rows = int(rows)
        self.bottle_volume = bottle_volume
        self.position_matrix = np.zeros((self.rows, self.columns), dtype=float)
        self.free_space = free_space


    def rack_space_free(self, row, column):
        #print('current rack space has volume', self.position_matrix[row, column], 'ml')
        if self.position_matrix[row, column] > 0:
            #print('rack space not free')
            return False
        else:
            return True
    
    def mark_rack_space_occupied(self, row, column, volume):
        #Ei ota vielä huomioon jos räkki menee täyteen
        #print('marking rack space occupied','row', row,'column', column, 'ml', volume)
        leftover = volume
        rows,columns,volumes = [],[],[]

        while leftover > 0:
            if leftover > (self.bottle_volume*(1-self.free_space)):
                injected_volume = self.bottle_volume*(1-self.free_space)
                leftover -= injected_volume
            else:
                injected_volume = leftover  
                leftover = 0 
                
            #print('marking rack space occupied', row, column, injected_volume, 'ml racktype', self.name, 'rack slot', self.slot)            
            self.position_matrix[row, column] += injected_volume
            rows.append(row)
            columns.append(column)
            volumes.append(injected_volume)
            
            if column+1 == self.columns:
                row += 1
                column = 0
            else:
                column += 1
            
            if row > self.rows:
                print('Not enough space in racks')
                raise Exception('Not enough space in racks')
        return rows,columns,volumes

class Rack_capacity_handler:
    def __init__(self, normal_racks=[], analysis_racks = [], heater_shaker_racks=[], solvent_racks=[]):
        self.normal_racks = normal_racks
        self.heater_shaker_racks = heater_shaker_racks
        self.analysis_racks = analysis_racks
        self.solvent_racks = solvent_racks
        self.tip_rack = None
        self.tip_rack_slot = None
        self.rack_place = {} #place for each component in form of {component: [[racks][rows][columns][volumes]]}


    def mark_rack_space_free(self, row, column):
        self.position_matrix[row, column] = 0

    def allocate_rack_for_component(self, component_name, component_volume):
        #print('allocating rack for', component_name, 'with volume', component_volume)
        if component_name in ['internal standard','ms', 'liquid catalyst', 'base'] or 'reactant' in component_name:
            ##print('normal rack', component_name)
            rack_list = self.normal_racks
            rack_type = 'normal_rack'
        elif component_name in ['solvent', 'analysis solvent']:
            rack_list = self.solvent_racks
            #modified to normal rack
            rack_type = 'solvent_rack'
        elif 'Reaction' in component_name:
            rack_list = self.heater_shaker_racks
            rack_type = 'heater_shaker_rack'
        elif 'analysis sample' in component_name:
            rack_list = self.normal_racks
            #modified to normal rack
            rack_type = 'normal_rack'
        elif component_name in ['product', 'reaction','reaction solution in analysis sample']:
            print('no rack allocated?', component_name)
            rack_type = ''
            return
        else:
            print(component_name)
            raise Exception('Component not recognized')
        #print('rack type', rack_type)
        #print('rack list', rack_list)
        for i, rack in enumerate(rack_list):
            for r in range(rack.rows):
                for c in range(rack.columns):
                    #print(f'testing if {component_name} fits in rack', rack.name, 'rack slot', rack.slot, 'in rows', r, 'in columns', c)
                    if rack.rack_space_free(r, c):
                        rows,columns,volumes = rack.mark_rack_space_occupied(r, c, component_volume)
                        self.rack_place[component_name] = {'racks':[rack_type+'_'+ str(i+1)], 'rows':rows, 'columns':columns, 'volumes':volumes}
                        #print('reserving', component_name, 'in rack', rack.name,'rack slot', rack.slot, 'in rows', rows, 'in columns', columns, 'in volumes', volumes)
                        return

   
    def find_destination(self, component):
        if component in self.rack_place:
            return self.rack_place[component]
        else:
            print(component)
            raise Exception('Component not found in rack_place')

    
    def find_source(self, component, volume):
        #print('finding source for', component, 'with volume', volume)
        position_indexes = []
        if component in self.rack_place:
            racks = self.rack_place[component]['racks']
            for rack in racks:
                rack_place = copy.deepcopy(self.rack_place[component])
                for i in range(len(self.rack_place[component]['volumes'])):
                    #if not enough volume in first position, empty it and move to next position
                    if self.rack_place[component]['volumes'][i] == 0:
                        continue
                    elif volume-0.01 > self.rack_place[component]['volumes'][i]:
                        #print('volume larger than position volume', volume, self.rack_place[component]['volumes'][i])
                        volume -= self.rack_place[component]['volumes'][i]
                        self.rack_place[component]['volumes'][i] = 0
                        position_indexes.append(i)
                    else:
                        #print('volume smaller than position volume', volume, self.rack_place[component]['volumes'])
                        self.rack_place[component]['volumes'][i] -= volume
                        position_indexes.append(i)
                        #print('volume smaller than position volume', volume, rack_place['volumes'])
                        return rack_place, position_indexes
            return rack_place, position_indexes
        else:
            raise Exception('Component not found in rack_place')
        