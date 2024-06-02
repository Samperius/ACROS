import pandas as pd
import numpy as np
from itertools import combinations
from ax.models.torch.botorch_modular.model import BoTorchModel
from ax.models.torch.botorch_modular.surrogate import Surrogate
from ax.models.torch.botorch_modular.acquisition import Acquisition
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy

from ax.modelbridge.registry import Models
from ax.modelbridge.factory import TorchModelBridge
from botorch.acquisition import qKnowledgeGradient
from ax.modelbridge.transforms import remove_fixed
from ax.modelbridge.transforms import unit_x

from ax.utils.notebook.plotting import render
from ax.runners.synthetic import SyntheticRunner

from botorch.models.model import Model
from botorch.models.gp_regression import FixedNoiseGP
from botorch.models.gp_regression import SingleTaskGP
from botorch.acquisition.monte_carlo import qExpectedImprovement, qNoisyExpectedImprovement
from botorch.acquisition.monte_carlo import qUpperConfidenceBound
from botorch.acquisition.monte_carlo import qProbabilityOfImprovement
from botorch.acquisition.logei import qLogExpectedImprovement, qLogNoisyExpectedImprovement

#import qLogExpectedImprovement
#from botorch.acquisition.logei import qLogExpectedImprovement

from botorch.acquisition.analytic import ProbabilityOfImprovement


from ax import Metric
from ax import Objective
from ax import SearchSpace
from ax import OptimizationConfig
from ax import Experiment
from ax import Data
from ax import Arm
from ax import RangeParameter, ParameterType, ChoiceParameter
from ax import Models

from ax.core.observation import ObservationFeatures, observations_from_data
from ax.plot.trace import optimization_trace_single_method
from ax.plot.pareto_frontier import plot_pareto_frontier
from ax.utils.notebook.plotting import render, init_notebook_plotting
from ax.plot.marginal_effects import plot_marginal_effects
from ax.plot.diagnostic import tile_cross_validation
from ax.plot.contour import plot_contour
from ax.plot.contour import interact_contour
from ax.plot.slice import plot_slice

class Reaction:
    #halutaan kuvaavan reaktion komponentit, niiden eq-suhteet ja moolimassat yms.
    def __init__(self,  reactants, products, solution_volume, analysis_volume=None, solvent= None, base_acids=None, catalysts=None, internal_standard = None, fixed_time=None, fixed_temperature=None, fixed_shaker_speed = None, reaction_solution=None, analysis_solvent=None, analysis_sample=None) -> None:
        self.reactants = reactants
        self.products = products 
        self.solution_volume = solution_volume
        self.solvent = solvent
        self.base_acids = base_acids
        self.catalysts = catalysts
        self.internal_standard = internal_standard
        self.fixed_time = fixed_time
        self.fixed_temperature = fixed_temperature
        self.fixed_shaker_speed = fixed_shaker_speed
        self.analysis_volume = analysis_volume
        self.reaction_solution = reaction_solution
        self.analysis_solvent = analysis_solvent      
        self.analysis_sample = analysis_sample

class Param:
    def __init__(self, name, type_, min=None, max=None, component = None, choices = None, optimize = True, eq=1, molar_mass = None, density = None, link =None, objective = False, fixed_value = None, unit = None) -> None:
        self.name = name
        self.min = min
        self.max = max
        self.component = component # component name e.g. solvent or product
        self.type = type_ #
        self.values = choices # categorical param values
        self.optimize = optimize
        self.eq = eq
        self.molar_mass = molar_mass
        self.density = density
        self.link = link
        self.objective = objective
        self.fixed_value = fixed_value
        self.unit = unit

class Axmodel:
    def __init__(self) -> None:
            self.experiment = None          
            self.data = None
            self.model = None
            self.sobol = None
            self.generator_run = None
            self.searchspace = None
            self.objective = None
            self.metric = None
            self.optimizationconfig = None
            self.trial = None
            self.params = None


    def create_experiment(self, name, params, minimize=False):
        search_space_parameters = []
        self.params = params
        for param in params:
            print(param.name, param.optimize, param.type, param.min, param.max, param.values)
            if param.type != 'choice' and param.optimize == 'yes':
                print('choice param', param.name, param.values, param.optimize, '= True')
                search_space_parameters.append(RangeParameter(name=param.name, parameter_type=ParameterType.FLOAT, lower=param.min, upper=param.max))
            elif param.type == 'choice'and param.optimize == 'yes':
                print('choice param', param.name, param.values, param.optimize, '= True')
                search_space_parameters.append(ChoiceParameter(name=param.name, parameter_type=ParameterType.STRING, values=param.values, is_ordered=False))

        self.search_space = SearchSpace(parameters = search_space_parameters)
        self.objective=Objective(Metric(name='objective'), minimize=minimize)  
        self.optimizationconfig = OptimizationConfig(objective=self.objective)
        self.experiment = Experiment(name=name,
                                    search_space=self.search_space,
                                    optimization_config=self.optimizationconfig,
                                    runner=SyntheticRunner())
        print('experiment created', self.experiment.parameters)

    def add_start_dataframe(self, params, df):
        print('df joka tulee add_start_dataframeen', df)
        self.trial = self.experiment.new_batch_trial()
        num_datapoints = df.shape[0]
        print('number of datapoints', num_datapoints)
        need_for_new_manual_batch = False
        build = False
        arm_datas = []
        start_params = {}
        previous_index = 0
        for arm_num in range(num_datapoints):
            print('arm_num', arm_num)
            current_index = df['trial_index'][arm_num]
            
            if df['mean'][arm_num] >= 0:
                pass
            else:
                print('no objective mean, new batch needed')
                need_for_new_manual_batch = True
                break
                
            if previous_index != current_index:
                self.trial.run().complete()
                self.trial = self.experiment.new_batch_trial()
    
            arm_name = f"{int(df['trial_index'][arm_num])}_{df['arm_index'][arm_num]}"
            for param in params:
                if param.optimize:
                    start_params[param.name] = df[param.name][arm_num]
            arm = Arm(parameters=start_params, name = arm_name)
            self.trial.add_arm(arm)
            arm_datas.append(
            {
                "arm_name": arm_name,
                "metric_name": "objective",
                "mean": df['mean'][arm_num],
                "sem": df['sem'][arm_num],
                "trial_index": df['trial_index'][arm_num]
            })
            previous_index = df['trial_index'][arm_num]
        if arm_datas != []:
            data = Data(df=pd.DataFrame.from_records(arm_datas))
            self.experiment.attach_data(data)
            build = True
        self.trial.run().complete()
        if need_for_new_manual_batch:
            self.add_manual_batch(params, df.iloc[arm_num:,:])
        return build
    
    def generate_sobol(self, batch_size, params,fix_temperature=False):
        self.sobol = Models.SOBOL(search_space=self.experiment.search_space, seed = 1234)
        if fix_temperature:
            fixed_temperature = (params[2].max + params[2].min)/2
            #starting_temperature = self.search_space.parameters[1].higher - self.search_space.parameters[1].lower
            self.generator_run = self.sobol.gen(
                                                n=batch_size
                                                , optimization_config=self.optimizationconfig
                                                , fixed_features=ObservationFeatures(parameters={"temperature": fixed_temperature})
                                                )
            
            self.trial = self.experiment.new_batch_trial(generator_run=self.generator_run)
        else:
            self.generator_run = self.sobol.gen(
                                                n=batch_size
                                                , optimization_config=self.optimizationconfig
                                                
                                                )
            
            self.trial = self.experiment.new_batch_trial(generator_run=self.generator_run)


    def build_model(self, function='qlogEI'):
        print('function is ', function)
        if function == 'qlogEI':
            model = qLogNoisyExpectedImprovement
            print('model is qlogEI')
        elif function == 'qEI':
            model = qExpectedImprovement
            print('model is qEI')
        elif function == 'qUCB':
            model = qUpperConfidenceBound
            print('model is qUCB')
        elif function == 'qPI':
            model = qProbabilityOfImprovement
        elif function == 'qRandom':
            self.model = Models.SOBOL(search_space=self.experiment.search_space, seed = 1234)
            print('model is qRandom')
            return
        
        self.model = Models.BOTORCH_MODULAR(search_space=self.experiment.search_space, 
                                    experiment=self.experiment,
                                    data=self.experiment.fetch_data(),
                                    surrogate=Surrogate(SingleTaskGP),  # Optional, will use default if unspecified
                                    botorch_acqf_class= model,  # Optional, will use default if unspecified
        )

    def render(self):
        categorical, params_without_categorical = self.params_without_categorical()
        param_combinations = self.return_param_combinations(len(params_without_categorical))
        if self.generator_run != None:
            gen_run = {'new':self.generator_run}
        else:
            gen_run = None
        if categorical is not None:
            print('param combinations', param_combinations)
            for cat_value in categorical:
                
                for combination in param_combinations:
#                    if combination[0] == 2 or combination[1] == 2:
#                        continue
                    render(plot_contour(model = self.model 
                                    ,param_x = params_without_categorical[combination[0]]
                                    ,param_y = params_without_categorical[combination[1]]
                                    ,generator_runs_dict=gen_run
                                    ,metric_name='objective'))
        else:
            print('no categorical vars, param combinations', param_combinations)

            for combination in param_combinations:
 #               if combination[0] == 2 or combination[1] == 2:
 #                   continue
                render(plot_contour(model = self.model 
                                    ,param_x = params_without_categorical[combination[0]]
                                    ,param_y = params_without_categorical[combination[1]]
                                    ,generator_runs_dict=gen_run
                                    ,metric_name='objective'))
                    
        render(plot_marginal_effects(model = self.model, metric='objective'))

        for param_name in params_without_categorical:
            if param_name != 'solvent':
                render(plot_slice(model=self.model,param_name = param_name, metric_name='objective'))

    def add_synthetic_results(self):
        results = []
        for arm_index in range(len(self.trial.arms)):
            arm = self.trial.arms[arm_index]
            arm_name = arm.name
            trial_num = int(arm_name.split('_')[0])
            result = self.synthetic_function(arm)
            results.append(result)
        self.add_results(results)


    def synthetic_function(self, arm):
        param1_value = arm.parameters['param 1']
        param2_value = arm.parameters['param 2']
        #param3_value = arm.parameters['param 3']
        return self.branin(param1_value, param2_value)

    def boha1(self, x1, x2):
        term1 = x1**2
        term2 = 2 * x2**2
        term3 = -0.3 * np.cos(3 * np.pi * x1)
        term4 = -0.4 * np.cos(4 * np.pi * x2)   
        y = term1 + term2 + term3 + term4 + 0.7
        return y

    def hartmann_3(self, x_1, x_2, x_3):
        xx = np.array([x_1, x_2, x_3])  # Combine inputs into an array
        # Constants
        alpha = np.array([1.0, 1.2, 3.0, 3.2])
        A = np.array([
            [3.0, 10, 30],
            [0.1, 10, 35],
            [3.0, 10, 30],
            [0.1, 10, 35]
        ])
        P = 10**(-4) * np.array([
            [3689, 1170, 2673],
            [4699, 4387, 7470],
            [1091, 8732, 5547],
            [381, 5743, 8828]
        ])

        xxmat = np.tile(xx, (4, 1))

        inner = np.sum(A[:, :3] * (xxmat - P[:, :3])**2, axis=1)
        outer = np.sum(alpha * np.exp(-inner))

        y = -outer
        return y
    

    def return_param_combinations(self, n_params):
        param_list = []
        for i in range(n_params):
            param_list.append(i)
        return list(combinations(param_list, 2))
    
    def params_without_categorical(self):
        params_without_categorical = []
        categorical = []
        for param in self.params:
            if param.type != 'choice' and param.optimize:
                params_without_categorical.append(param.name)
                print('param', param.name, 'is not categorical and optimize = True')
            elif param.type == 'choice' and param.optimize:
                print('param', param.name, 'is categorical or optimize = True')
                categorical.append(param.name)
        if categorical == []:
            categorical = None
        return categorical, params_without_categorical

    def return_param_combinations(self, n_params):
        param_list = []
        for i in range(n_params):
            param_list.append(i)
        return list(combinations(param_list, 2))
                            
    def new_batch(self, n, fixed_temperature = False):
        if fixed_temperature:
            sample = self.model.gen(1)
            generated_temperature = sample.arms[0].parameters['temperature']
            print('generating batch', sample.arms)
            self.generator_run = self.model.gen(
                n = n,
                    optimization_config=self.optimizationconfig,
                    fixed_features=ObservationFeatures(parameters={"temperature": generated_temperature}),
                                                )
            self.trial = self.experiment.new_batch_trial(generator_run=self.generator_run)
        else:
            print('generating batch no fixed temperature')
            self.generator_run = self.model.gen(
                n = n,
                    optimization_config=self.optimizationconfig,

                    )
            self.trial = self.experiment.new_batch_trial(generator_run=self.generator_run)
    
    def new_manual_batch(self, arm_datas):
        arms = []
        for arm_index, arm in enumerate(arm_datas):
            arm = Arm(parameters=arm, name=str(self.trial.index+1) + '_' + str(arm_index))
            arms.append(arm)
        self.trial = self.experiment.new_batch_trial().add_arms_and_weights(arms=arms)
        print(arms)
   
    def add_manual_batch(self, params, df):
        self.trial = self.experiment.new_batch_trial()
        num_datapoints = df.shape[0]
        df = df.reset_index(drop=True)
        start_params = {}
        arm_datas = []
        for arm_num in range(num_datapoints):
            arm_name = f"{df['arm_name'][arm_num]}"
            for param in params:
                if param.optimize:
                    start_params[param.name] = df[param.name][arm_num]
            arm = Arm(parameters=start_params, name = arm_name)
            self.trial.add_arm(arm)

    def render_new_batch(self, param_names):
        categorical, params_without_categorical = self.params_without_categorical()
        param_combinations = self.return_param_combinations(len(params_without_categorical))
        print(param_combinations)
        print("model", self.model)
        if categorical is not None:
            for cat_value in categorical.values:
                for combination in param_combinations:
                    if combination[0] == 2 or combination[1] == 2:
                        continue
                    render(plot_contour(model = self.model 
                                    ,param_x = param_names[combination[0]]
                                    ,param_y = param_names[combination[1]]
                                    ,generator_runs_dict={'new':self.generator_run} 
                                    ,metric_name='objective')
                                    )
        else:
            for combination in param_combinations:
                if combination[0] == 2 or combination[1] == 2:
                    continue
                if self.generator_run == None:
                    render(plot_contour(model = self.model 
                                        ,param_x = param_names[combination[0]]
                                        ,param_y = param_names[combination[1]]
                                        ,metric_name='objective')
                                        #,title = f"{categorical.name} = {cat_value}"
                                        )
                else:
                    render(plot_contour(model = self.model 
                                        ,param_x = param_names[combination[0]]
                                        ,param_y = param_names[combination[1]]
                                        ,generator_runs_dict={'new':self.generator_run} 
                                        ,metric_name='objective')
                                        #,title = f"{categorical.name} = {cat_value}"
                                        )
                    
        render(plot_marginal_effects(model = self.model, metric='objective'))
        for param_name in param_names:
            if param_name != 'solvent':
                render(plot_slice(model=self.model,param_name = param_name, metric_name='objective'))
            
    def query_results_from_user(self):
        results = []
        for arm_index in range(len(self.trial.arms)):
            print(f"Please enter the results for arm {arm_index}, with params {self.trial.arms[arm_index].parameters}")
            try:
                results.append(float(input()))
            
            except ValueError:
                print("Please enter a number")
                results.append(float(input()))
        return results
    
    def add_results(self,results):
        n = len(self.trial.arms)
        arm_datas = []
        for arm_num in range(n):
            arm = self.trial.arms[arm_num]
            arm_name = arm.name
            trial_num = int(arm_name.split('_')[0])
            #if type(results) == list:
            result = results[arm_num]
            arm_datas.append(
            {
                "arm_name": arm_name,
                "metric_name": "yield",
                "mean": result,
                "sem": None,
                "trial_index": trial_num
            })
        
        data = Data(df=pd.DataFrame.from_records(arm_datas))
        self.experiment.attach_data(data)
        self.trial.run().complete()


    def optimization_test_function(self, x_1, x_2):
        return x_1**2 + x_2**2
    
    def add__test_results(self,results):
        n = len(self.trial.arms)
        arm_datas = []
        for arm_num in range(n):
            arm = self.trial.arms[arm_num]
            arm_name = arm.name
            trial_num = int(arm_name.split('_')[0])
            #if type(results) == list:
            result = results[arm_num]
            arm_datas.append(
            {
                "arm_name": arm_name,
                "metric_name": "objective",
                "mean": result,
                "sem": 0,
                "trial_index": trial_num
            })
        
        data = Data(df=pd.DataFrame.from_records(arm_datas))
        self.experiment.attach_data(data)
        self.trial.run().complete()

