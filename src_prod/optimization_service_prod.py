import pandas as pd
import sys
from config_prod import INITIAL_FILE_PATH, SAVE_FILE_PATH
from  ax_model_prod import Axmodel, Param, Reaction
import numpy as np



class OptimizationService:
    def __init__(self) -> None:
        self.axmodel = Axmodel()
        self.df = None
        self.params = []
    
    def create_params(self, param_data):
        self.params = []
        for i, param in enumerate(param_data):
            if i>0:
                if param[11]:
                    #choice values are separated by comma
                    values = param[11].strip()
                    values = values.split(',')
                else:
                     values = None
                
                self.params.append(Param(name = param[0], component=param[1], optimize = param[2], objective = param[3], type_ =param[4], link = param[5], eq = param[6], molar_mass = param[7], density = param[8],min = param[9], max = param[10], choices = values, fixed_value = param[12], unit = param[13]))


    def create_reaction(self, solution_volume, analysis_volume):
        reactants = []
        products = []
        solvent = None
        base_acids = []
        catalysts = []
        time = None
        temperature = None
        internal_standard = None
        shaker_speed = None
        reaction_solution = None
        analysis_solvent = None
        analysis_sample = None

        for param in self.params:
            print(param.name, param.component)
            if param.component == 'reagent':
                reactants.append(param)
            if param.component == 'product':
                products.append(param)
            if param.component == 'solvent':
                solvent = param
            if param.component == 'base' or param.component == 'acid':
                base_acids.append(param)
            if 'catalyst' in param.component:
                catalysts.append(param)
            if param.name == 'time':
                time = param.fixed_value
            if param.name == 'temperature':
                temperature = param.fixed_value
            if param.name == 'shaker speed':
                shaker_speed = param.fixed_value
            if param.component == 'internal standard':
                print('internal standard', param)
                internal_standard = param
            if param.component == 'reaction solution in analysis sample':
                print('reaction solution', param)
                reaction_solution = param
            if param.component == 'analysis solvent':
                print('analysis', param)
                analysis_solvent = param
            if param.component == 'analysis sample':
                print('analysis sample', param)
                analysis_sample = param       
        self.reaction = Reaction(reactants=reactants, products=products, solution_volume=solution_volume, analysis_volume= analysis_volume, solvent=solvent, base_acids=base_acids, catalysts=catalysts, fixed_time=time, fixed_temperature=temperature, internal_standard = internal_standard, fixed_shaker_speed = shaker_speed,reaction_solution = reaction_solution, analysis_solvent = analysis_solvent, analysis_sample = analysis_sample)

    def create_experiment(self, model_name, minimize):
        self.axmodel.experiment = None
        self.axmodel.create_experiment(model_name, self.params, minimize=minimize)

    def build_model_with_initial_data(self, params, filepath, minimize = False):
        if filepath.endswith('.csv'):
            df= pd.read_csv(filepath)            
        elif filepath.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        
        df['arm_index'] = df['arm_name'].apply(lambda x: x.split('_')[1])    
        self.df = df.iloc[:,:-3]
        print('data joka haluttaisiin experimenttiin: ', self.df.iloc[3:,:])
        self.create_experiment('some', minimize)
        build = self.axmodel.add_start_dataframe(params, df)
        print('experiment nyt ennen buildausta', self.axmodel.experiment.fetch_data().df)
        #if build:
        self.axmodel.build_model()
        
    def build_model_with_random_points(self, model_name, params, batch_size, fix_temperature):
        self.axmodel.create_experiment(model_name, self.params)
        self.axmodel.generate_sobol(batch_size, self.params, fix_temperature)
        print('new batch is created', self.axmodel.trial.arms)

    def add_manual_batch(self, model_name, params):
        self.axmodel.create_experiment(model_name, params)
        df = pd.read_excel(INITIAL_FILE_PATH)
        self.axmodel.add_manual_batch(params, df)
        print(self.axmodel.experiment.fetch_data().df)
        print('new batch is created', self.axmodel.trial.arms)

    def render_all(self):
        self.axmodel.render()

    def render_new_batch(self, param_names):
        self.axmodel.render_new_batch(param_names)

    def build_model(self, function=None):
        self.axmodel.build_model(function=function)
        print(self.axmodel.experiment.fetch_data().df)

    def new_batch(self, n, fixed_temperature):
        self.axmodel.new_batch(n, fixed_temperature)
        print('new batch is created', self.axmodel.trial.arms)

    def return_params(self):
        return self.axmodel.params
    
    def return_params_values(self, key):
        values = []
        for param in self.axmodel.params:
            if param.optimize:
                values.append(param.name)
        return values
    
    def synthetic_data_algorithm(self, n_batch, batch_size, function=None, save_path=None):
        for i in range(n_batch):
            if self.axmodel.model is None:
                self.axmodel.generate_sobol(batch_size, self.params)
            else:
                self.axmodel.new_batch(batch_size)
            self.axmodel.add_synthetic_results()
            self.build_model(function=function)
            print('current min ', self.axmodel.experiment.fetch_data().df['mean'].min())
            if self.axmodel.experiment.fetch_data().df['mean'].min() < 0.4:
                print('optimal reached')
                break
        print('saving experiment with path ', save_path)
        self.save_experiment(save_path)

        print('synthetic data algorithm with function {function} and batchsize {batch_size} is completed')

    def save_experiment(self, save_path):
        for j, element in enumerate(self.axmodel.experiment.trials.items()):
            trial = element[1]
            for i,arm in enumerate(trial.arms):
                if i == 0 and j == 0:
                    arm_name = pd.DataFrame({'arm_name': [arm.name]})
                    df = pd.DataFrame(arm.parameters, index=[0])
                    #df = pd.concat([arm_name, df], ignore_index=False, axis=1)
                else:
                    df2 = pd.DataFrame(arm.parameters, index=[0])
                    arm_name2 = pd.DataFrame({'arm_name': [arm.name]})
                    arm_name = pd.concat([arm_name, arm_name2], ignore_index=True, axis=0)
                    df = pd.concat([df, df2], ignore_index=True, axis=0)
        df = pd.concat([arm_name, df], ignore_index=False, axis=1)
        results = self.axmodel.experiment.fetch_data().df
        results = results.drop(['arm_name'], axis=1)
        #results.rename(columns={'mean': 'yield_mean'}, inplace=True)
        joined = pd.concat([df, results], ignore_index=False, axis=1)
        joined['trial_index'] = joined['arm_name'].apply(lambda x: x.split('_')[0] if len(x.split('_'))>1 else '')
        joined.to_excel(save_path, index=False)

    def return_arms(self):
        return self.axmodel.trial.arms
    
    def update_model_with_batch_results(self,results):
        self.axmodel.add_results(results)
        print(self.axmodel.experiment.fetch_data().df)
        self.axmodel.build_model()
    
    def updata_model_with_test_results(self):
        print(self.axmodel.experiment.fetch_data().df)

    def calculate_yields(self, concentrations, combined_solutions):
        analysis_product_volume = 0.1
        #reaction solution concentration = concentration of analysis_sample * (dilution factor)
        extra_dilution_factor = np.array([4,4,4,4])
        c_reaction_solution = concentrations * (combined_solutions[0].analysis_volume/analysis_product_volume)*extra_dilution_factor
        print('concentrations', concentrations)
        print('dilution factor', combined_solutions[0].analysis_volume/analysis_product_volume)
        print('c_reaction_solution', c_reaction_solution)
        total_mass = combined_solutions[0].solution_volume * c_reaction_solution
        theor_mass = []
        for combined_solution in combined_solutions:
            theor_mass.append(combined_solution.product_mass)
        print('theor_mass', theor_mass)
        print('total_mass', total_mass)
        yield_percent = total_mass / np.array(theor_mass)*100
        print('yield', yield_percent)
        #should be return yield_percent
        return yield_percent