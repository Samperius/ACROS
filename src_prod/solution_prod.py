class Solution:
    def __init__(self, solution_volume=None, solution_molar_concentration = None, solution_mass_concentration = None) -> None:
        self.solution_volume = solution_volume
        self.solution_molar_concentration = solution_molar_concentration
        #mass concentration = mg / mL
        self.solution_mass_per_volume_concentration = solution_mass_concentration
        #molecular weight = mg / mmol
        self.solution_molecular_weight = None
        self.reactant_name = None
        self.reactant_mass = None
        self.reactant_volume = None
        #density = mg / mL
        self.reactant_density = None
        self.reactant_amount = None
        self.reactant_molar_concentration = None
        self.reactant_mass_per_volume_concentration = None
        self.reactant_molecular_weight = None
        self.reactant_mass_per_solvent_mass_ratio = None
        self.reactant_mass_per_solution_mass_ratio = None
        self.location = None
        self.reactant_equivalent_ratio = None
    
    def calculate_solution_volume(self):
        if self.solvent_volume != None and self.reactant_volume != None:
            self.solution_volume = self.solvent_volume + self.reactant_volume
        
        elif self.solvent_volume == None:
            self.calculate_solvent_volume()
            self.solution_volume = self.solvent_volume + self.reactant_volume
        
        elif self.reactant_volume == None:
            self.calculate_reactant_volume()
            self.solution_volume = self.solvent_volume + self.reactant_volume
    
    def calculate_missing_solution_concentration(self):
        # if other concentration is known, calculate missing concentration
        if self.solution_mass_per_volume_concentration == None:
            self.solution_mass_per_volume_concentration = self.solution_molar_concentration * self.reactant_molecular_weight
        
        elif self.solution_molar_concentration == None:
            self.solution_molar_concentration = self.solution_mass_per_volume_concentration / self.reactant_molecular_weight
        pass

    def calculate_missing_reactant_concentration(self):
        # if other concentration is known, calculate missing concentration
        if self.reactant_mass_per_volume_concentration != None:
            self.reactant_molar_concentration = self.reactant_mass_per_volume_concentration / self.reactant_molecular_weight

        elif self.reactant_molar_concentration != None:
            self.reactant_mass_per_volume_concentration = self.reactant_molar_concentration * self.reactant_molecular_weight

        elif self.reactant_mass_per_solvent_mass_ratio != None:
            pass
        pass

    def calculate_reactant_amount(self, fixed_value = None):
        if self.solution_volume != None and self.solution_molar_concentration != None:
            
            if fixed_value == None:
                self.reactant_amount = self.solution_volume * self.solution_molar_concentration
            else:
                self.reactant_amount = fixed_value
        if self.reactant_mass != None and self.reactant_molecular_weight != None:
            self.reactant_amount = self.reactant_mass / self.reactant_molecular_weight
        

    def calculate_reactant_volume(self, dilution_factor=None):
        print('calculate reactant volume')
        print('reactant molar concentration', self.reactant_molar_concentration)
        print('reactant mass per volume concentration', self.reactant_mass_per_volume_concentration)
        print('reactant density', self.reactant_density)

        if self.reactant_molar_concentration != None:
            self.reactant_volume = self.reactant_amount / self.reactant_molar_concentration
        elif self.reactant_mass_per_volume_concentration != None:
            self.reactant_volume = self.reactant_mass / self.reactant_mass_per_volume_concentration
        elif self.reactant_density != None:
            self.reactant_volume = self.reactant_mass / (self.reactant_density*1000)
        #if mother solution dilution factor is known, calculate diluted reactant volume
        if dilution_factor != None:
            print('dilution factor', dilution_factor)
            self.reactant_volume = self.reactant_volume * dilution_factor
        print('reactant volume', self.reactant_volume)
        

    def calculate_reactant_mass(self):
        if self.reactant_mass == None and self.reactant_amount != None and self.reactant_molecular_weight != None:
            self.reactant_mass = self.reactant_amount * self.reactant_molecular_weight
        
    def calculate_solvent_volume(self):

        if self.solvent_density != None:
            if self.solvent_mass == None:
                self.calculate_solvent_mass()
            self.solvent_volume = self.solvent_mass / self.solvent_density

        elif self.solution_volume != None and self.reactant_volume != None:
            self.solvent_volume = self.solution_volume - self.reactant_volume
        
        else:
            raise Exception('solvent volume cannot be calculated')
                
        #Calculate mass of solvent needed to make solution after reactant is known
    def calculate_solvent_mass(self):
        if self.reactant_mass_per_solvent_mass_ratio != None and self.reactant_mass != None:
            self.solvent_mass = self.reactant_mass / self.reactant_mass_per_solvent_mass_ratio
        pass
        #Calculate amount of solvent needed to make solution after reactant is known
    def calculate_solvent_amount(self):
        pass
        #self.solvent_amount = self.solvent_mass / self.solvent_molecular_weight

    def return_reactant_volume(self):
        return self.reactant_volume





class CombinedSolution:
    def __init__(self, solutions, solution_volume ) -> None:
        self.solutions = solutions
        self.solvent_volume = 0
        self.solution_volume = 0
        self.total_reactant_volume = 0
        self.reactant_volumes = {}
        self.solution_volume = solution_volume
        self.product_volumes = []
        self.product_amounts = []
        self.product_molar_concentrations = []
        self.product_masses = []
        self.product_mass_per_volume_concentration = []
        self.product_molecular_weights = []
        self.product_equivalent_ratios = []
        self.analysis_volume = None
        self.analysis_product_volume = None
        self.analysis_dilute_volume = None
        self.internal_standard_volume = None
        self.catalyst_masses = None
        self.catalyst_volumes = None
        self.catalyst_amounts = None
        self.catalyst_densities = None
        self.base_acid_masses = None
        self.base_acid_volumes = None
        self.base_acid_amounts = None
        self.base_acid_densities = None       

    def calculate_total_reactant_volume(self):
        self.total_reactant_volume = 0
        for solution in self.solutions:
            self.total_reactant_volume += solution.return_reactant_volume()

    def calculate_solvent_volume(self, fixed_value = None):
        if fixed_value != None:
            self.solvent_volume = fixed_value
            return
        self.solvent_volume = self.solution_volume - self.total_reactant_volume
        for i in range(len(self.catalyst_volumes)):
            self.solvent_volume -= self.catalyst_volumes[i]
        
        for j in range(len(self.base_acid_volumes)):
            self.solvent_volume -= self.base_acid_volumes[j]

    def update_solution_reactants(self):
        for i, solution in enumerate(self.solutions):
            self.reactant_volumes[solution.reactant_name] = solution.return_reactant_volume()

    def calculate_solution_volume(self):
        self.solution_volume = self.solvent_volume + self.total_reactant_volume + self.catalyst_volume

    def calculate_product_amount(self, products, fixed_amount = None):
        for product in products:
            if product.fixed_amount != None:
                self.product_amounts.append(fixed_amount)
            return
        #for i in range(len(self.product_equivalent_ratios)):
            #self.product_amounts.append( * self.product_equivalent_ratios[i])


    def calculate_product_molar_concentration(self):
        for i in range(len(self.product_amounts)):
            self.product_molar_concentrations.append(self.product_amounts[i] / self.solution_volume)

    def calculate_product_mass(self):
        for i in range(len(self.product_amounts)):
            self.product_masses.append(self.product_amounts[i] * self.product_molecular_weights[i])
    
    def calculate_product_volume(self):
        for i in range(len(self.product_amounts)):
            self.product_volumes.append(self.product_amounts[i] / self.product_molar_concentrations[i])
    
    def calculate_product_mass_per_volume_concentration(self):
        self.product_mass_per_volume_concentrations = []
        for i in range(len(self.product_amounts)):
            self.product_mass_per_volume_concentrations.append(self.product_masses[i] / self.solution_volume)

    def calculate_analysis_product_volume(self, analysis_dilution_ratio):
        self.analysis_product_volume = self.analysis_volume * analysis_dilution_ratio
    
    def calculate_analysis_dilute_volume(self,analysis_dilution_ratio):
        self.analysis_dilute_volume = self.analysis_volume * (1 - analysis_dilution_ratio)-self.internal_standard_volume
        
    def calculate_catalyst_volumes(self):
        if self.catalyst_masses != None:
            for i, catalyst_mass in enumerate(self.catalyst_masses):
                self.catalyst_volumes[i] = catalyst_mass / self.catalyst_densities[i]
    
    def calculate_analysis_dilution_ratio(self):
        self.analysis_dilution_ratio = 1
        for product_mass_per_volume in self.product_mass_per_volume_concentrations:
            analysis_dilution_ratio = 1/product_mass_per_volume
            if analysis_dilution_ratio < self.analysis_dilution_ratio:
                self.analysis_dilution_ratio = analysis_dilution_ratio

            
    
class MotherSolutions:
    def __init__(self, reaction) -> None:
        self.reaction = reaction
        
    def return_linked_reactant(self, reactant):
        for reactant_candidate in self.reaction.reactants:
            if reactant_candidate.name == reactant.link:
                return reactant_candidate
        raise Exception('linked reactant not found')
    

    def calculate_mother_solutions(self):
        #calculate min volume based on min amount of reactant lower bound
        for reactant in self.reaction.reactants:
            if reactant.optimize == 'yes':
                param_min_volume = reactant.min * self.reaction.solution_volume * reactant.molar_mass / (reactant.density*1000)
           
            else:
                param_min_volume = self.return_linked_reactant(reactant).min * self.reaction.solution_volume * reactant.molar_mass / (reactant.density*1000)
            
            if param_min_volume < 0.1:
                reactant.ms_dilution_factor = 0.1 / param_min_volume
            else:
                reactant.ms_dilution_factor = 1
            
            print('reactant', reactant.name ,'factor', reactant.ms_dilution_factor)
        return self.reaction
        
                           