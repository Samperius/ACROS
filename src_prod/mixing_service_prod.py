from solution_prod import Solution, CombinedSolution, MotherSolutions

class Mixing_combined_solution:
    def __init__(self, reaction, arms, ms) -> None:
        self.reaction = reaction
        self.combined_solutions = []
        self.solution_volume = reaction.solution_volume
        self.analysis_volume = reaction.analysis_volume
        self.solution_concentrations = None
        self.reactant_molecular_weights = []
        self.reactant_molar_concentrations = []
        self.reactant_densities = []
        self.arms = arms
        self.reactant_eq_ratios = []
        self.ms = ms
        if self.ms:
            self._calculate_mother_solutions()
        self._initialize_solutions()
        self.analysis_volume = 2
        

    def _calculate_mother_solutions(self):
        print('calculating mother solutions')
        self.ms = MotherSolutions(self.reaction)
        self.reaction = self.ms.calculate_mother_solutions()
    
    def update_molar_masses(self):
        if self.reaction.reactants != None:
            return
        for reactant in self.reaction.reactants:
                self.reactant_molecular_weights.append(reactant.molar_mass)
        
    def update_molar_concentrations_and_densities(self):
        if self.reaction.reactants != None:
            return
        for reactant in self.reaction.reactants:
            if reactant.molar_concentration != None:
                self.reactant_molar_concentrations.append(reactant.molar_concentration)
            else:
                self.reactant_molar_concentrations.append(self.density_to_molar_concentration(reactant))

            if reactant.density != None:
                self.reactant_densities.append(reactant.density)
            
            else:
                self.reactant_densities.append(self.molar_concentration_to_density(reactant))
            
    def calculate_eq_ratios(self):
        pass


    def density_to_molar_concentration(self, reactant):
        reactant.molar_concentration = reactant.density*1000 / (reactant.molar_mass)
        return reactant.molar_concentration
    
    def molar_concentration_to_density(self, reactant, reaction_volume = None ):
        #if volume and moles are known, molar concentration could be calculated
        if reactant.fixed_value != None and reaction_volume != None:
            reactant.molar_concentration = reactant.fixed_value / reaction_volume
            print('reactant mols ', reactant.fixed_value)
            print('reaction volume ', reaction_volume)
            print('reactant molar concentration ', reactant.molar_concentration)
        reactant.density = reactant.molar_concentration * (reactant.molar_mass) / 1000
        print('density', reactant.density)
        return reactant.density

    def return_eq_ratio(self, component):
        if component.link:
            link_name = component.link
            for reactant_ in self.reaction.reactants:
                if reactant_.name == link_name:
                    return component.eq/reactant_.eq
        else:
            return 1


    def _initialize_solutions(self):
        #different samples/arms to be mixed
        for arm_i in range(len(self.arms)):
            solutions = []
            #different reactants in the sample/arms
            for i, reactant in enumerate(self.reaction.reactants):
                eq_ratio = self.return_eq_ratio(reactant)
                if reactant.link:
                    solution_molar_concentration = eq_ratio*self.arms[arm_i].parameters[reactant.link]
                elif reactant.fixed_value:
                    solution_molar_concentration = reactant.fixed_value
                        
                
                solution = Solution(solution_volume = self.reaction.solution_volume, solution_molar_concentration = solution_molar_concentration)
                if reactant.molar_mass:
                    solution.reactant_molecular_weight = reactant.molar_mass
                else:
                    self.density_to_molar_concentration(reactant)
                if reactant.density:
                    solution.reactant_density = reactant.density
                else:
                    print('please insert density of', reactant.name)
                    raise Exception('density not found')
                    #solution.reactant_density = self.molar_concentration_to_density(reactant, reaction_volume=self.reaction.solution_volume)
                        
                solution.reactant_name = reactant.name
                solution.reactant_equivalent_ratio = eq_ratio
                if reactant.fixed_value:
                    solution.calculate_reactant_amount(reactant.fixed_value)
                else:
                    solution.calculate_reactant_amount()
                solution.calculate_reactant_mass()
                if self.ms:
                    print('ms')
                    solution.calculate_reactant_volume(reactant.ms_dilution_factor)
                else:
                    solution.calculate_reactant_volume()
                solutions.append(solution)
            
            
            combined_solution = CombinedSolution(solutions, self.reaction.solution_volume)
            if self.reaction.fixed_time:
                combined_solution.time = self.reaction.fixed_time
            else:
                combined_solution.time = self.arms[arm_i].parameters['time']
            if self.reaction.fixed_temperature == 'yes':
                combined_solution.temperature = self.reaction.fixed_temperature
            else:
                combined_solution.temperature = self.arms[arm_i].parameters['temperature']

            if self.reaction.fixed_shaker_speed:
                combined_solution.shaker_speed = self.reaction.fixed_shaker_speed
            else:
                combined_solution.shaker_speed = self.arms[arm_i].parameters['shaker speed']

            if self.reaction.internal_standard.fixed_value:
                combined_solution.internal_standard_volume = self.reaction.internal_standard.fixed_value
            else:
                print('internal standard none', self.reaction.internal_standard.name) 
                combined_solution.internal_standard_volume = None
            
            catalyst_mols, catalyst_masses, catalyst_volumes = self.return_catalyst_massses_and_volumes(arm_i, solutions)
            combined_solution.catalyst_masses = catalyst_masses
            combined_solution.catalyst_volumes = catalyst_volumes
            combined_solution.catalyst_amounts = catalyst_mols
    
            base_acid_mols, base_acid_masses, base_acid_volumes = self.return_base_acid_massses_and_volumes(arm_i, solutions)
            combined_solution.base_acid_masses = base_acid_masses
            combined_solution.base_acid_volumes = base_acid_volumes
            combined_solution.base_acid_amounts = base_acid_mols

            eq_ratios, product_mols, product_molar_masses = self.return_product_info(arm_i)
            combined_solution.product_equivalent_ratios = eq_ratios
            combined_solution.product_amounts = product_mols
            combined_solution.product_molecular_weights = product_molar_masses

            combined_solution.analysis_volume = self.analysis_volume
            combined_solution.update_solution_reactants()
            combined_solution.calculate_total_reactant_volume()
            if self.reaction.solvent.fixed_value:
                combined_solution.calculate_solvent_volume(fixed_value=self.reaction.solvent.fixed_value)
            else:
                combined_solution.calculate_solvent_volume()
            combined_solution.calculate_product_molar_concentration()
            combined_solution.calculate_product_mass()
            combined_solution.calculate_product_mass_per_volume_concentration()
            combined_solution.calculate_product_volume()
            combined_solution.calculate_analysis_dilution_ratio()
            combined_solution.calculate_analysis_product_volume(combined_solution.analysis_dilution_ratio)
            combined_solution.calculate_analysis_dilute_volume(combined_solution.analysis_dilution_ratio)
            self.combined_solutions.append(combined_solution)
    
    def return_product_info(self,arm_i):
        eq_ratios = []
        product_mols = []
        product_molar_masses = []
        for product in self.reaction.products:
            eq_ratio = self.return_eq_ratio(product)
            eq_ratios.append(eq_ratio)
            print('product', product.name, product.link, product.molar_mass)
            try:
                product_mols.append(eq_ratio*self.arms[arm_i].parameters[product.link]*self.reaction.solution_volume)
            except:
                for reactant in self.reaction.reactants:
                    if reactant.name == product.link:
                        product_mols.append(eq_ratio*reactant.fixed_value)
                        break
            product_molar_masses.append(product.molar_mass)
        return eq_ratios, product_mols, product_molar_masses
    
    def return_catalyst_massses_and_volumes(self, arm_i, solutions):
            catalyst_masses = []
            catalyst_volumes = []
            catalyst_mols = []
            for catalyst in self.reaction.catalysts:
                linked_reactant = self.return_linked_reactant(catalyst.link)
                if catalyst.optimize == 'yes':
                        for solution in solutions:
                                
                                if solution.reactant_name == linked_reactant.name and catalyst.unit == 'mol-%':
                                    mols = solution.reactant_amount*self.arms[arm_i].parameters[catalyst.name]
                                elif solution.reactant_name == linked_reactant.name and catalyst.unit == 'mass-%':
                                    mols = solution.reactant_mass*self.arms[arm_i].parameters[catalyst.name] / catalyst.molar_mass  

                else:
                    eq_ratio = self.return_eq_ratio(catalyst) 
                    for solution in solutions:
                        if solution.reactant_name == linked_reactant.name and catalyst.unit == 'mol-%':
                            mols = solution.reactant_amount*eq_ratio
                        elif solution.reactant_name == linked_reactant.name and catalyst.unit == 'mass-%':
                            mols = solution.reactant_mass*eq_ratio
                if not catalyst:
                    raise Exception('Catalyst not recognized')
                catalyst_mols.append(mols)
                catalyst_masses.append(mols*catalyst.molar_mass)
                catalyst_volumes.append(mols*catalyst.molar_mass/(catalyst.density*1000))               
            return catalyst_mols, catalyst_masses, catalyst_volumes

    def return_base_acid_massses_and_volumes(self, arm_i, solutions):
            base_acid_masses = []
            base_acid_volumes = []
            base_acid_mols = []
            for base_acid in self.reaction.base_acids:
                if base_acid.link:
                    linked_reactant = self.return_linked_reactant(base_acid.link)
                if base_acid.optimize == 'yes':
                        for solution in solutions:
                                if base_acid.fixed_value:
                                    mols = base_acid.fixed_value
                                elif solution.reactant_name == linked_reactant.name and base_acid.unit == 'mol-%':
                                    mols = solution.reactant_amount*self.arms[arm_i].parameters[base_acid.name]
                                elif solution.reactant_name == linked_reactant.name and base_acid.unit == 'mass-%':
                                    mols = solution.reactant_mass*self.arms[arm_i].parameters[base_acid.name]/(base_acid.molar_mass)
                                else:
                                    raise Exception('base_acid unit not recognized')

                elif base_acid.fixed_value:
                    mols = base_acid.fixed_value
                else:
                    eq_ratio = self.return_eq_ratio(base_acid)
                    for solution in solutions:
                        if solution.reactant_name == linked_reactant.name and base_acid.unit == 'mol-%':
                            mols = solution.reactant_amount*eq_ratio
                        elif solution.reactant_name == linked_reactant.name and base_acid.unit == 'mass-%':
                            mols = solution.reactant_mass*eq_ratio
                base_acid_mols.append(mols)
                base_acid_masses.append(mols*base_acid.molar_mass)
                base_acid_volumes.append(mols*base_acid.molar_mass/(base_acid.density*1000))
            return base_acid_mols, base_acid_masses, base_acid_volumes


    def return_linked_reactant(self,linked_name):
        print('linked', linked_name)
        for reactant in self.reaction.reactants:
            print(reactant.name)
            if reactant.name == linked_name:
                return reactant
        raise Exception('Linked reactant not found')