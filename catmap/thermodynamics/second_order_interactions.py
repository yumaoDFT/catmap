import catmap
from catmap import ReactionModelWrapper
from catmap.model import ReactionModel
from catmap.functions import smooth_piecewise_linear
from catmap.functions import offset_smooth_piecewise_linear
from catmap.functions import parse_constraint
from catmap.thermodynamics import FirstOrderInteractions
import pylab as plt
import numpy as np
from scipy import integrate

class SecondOrderInteractions(FirstOrderInteractions,ReactionModelWrapper):
    """Class for implementing 'first-order adsorbate interaction model. 
    Should be sub-classed by scaler."""

    def __init__(self,reaction_model=ReactionModel()):
        FirstOrderInteractions.__init__(self,reaction_model)

    def integral_interaction_function(self,coverages,energies,epsilon,
            F,include_derivatives=False):

        #Allow the argument for consistency, but it should always be false
        if include_derivatives:
            raise ValueError('Derivatives not supported for integral energy')
       
        N_ads = len(coverages)
        #for site_info_dict on the fly since speed isn't very important here 
        # (function is only called during fitting, not solving)
        site_info_dict = {}
        surf_species = self.adsorbate_names+self.transition_state_names
        for s in self.site_names:
            idxs = [surf_species.index(a) for a in surf_species if
                    self.species_definitions[a]['site'] == s]
            if idxs:
                if self.adsorbate_interaction_model not in ['ideal',None]:
                    default_params = getattr(
                            self.thermodynamics.adsorbate_interactions,
                            'interaction_response_parameters',{})
                else:
                    default_params = {}
                F_params = self.species_definitions[s].get('interaction_response_parameters',default_params)
                site_info_dict[s] = [idxs,self.species_definitions[s]['total'],F_params]
        
        idx_lists = []
        f = []
        df = []
        d2f = []
        all_adsnames = self.adsorbate_names + self.transition_state_names
        sum_1 = np.dot(coverages,energies)
        for ads in all_adsnames:
            adsname, s = ads.rsplit('_',1)
            idxs,max_cvg,F_params = site_info_dict[s]
            F_params = F_params.copy()
            if 'max_coverage' not in F_params:
                F_params['max_coverage'] = max_cvg
            else:
                F_params['max_coverage'] *= max_cvg
            theta_tot = sum([coverages[i] for i in idxs])
            fs,dfs,d2fs = F(theta_tot,**F_params)
            f.append(fs)
            df.append(dfs)
            d2f.append(d2fs)
        
        for i in range(len(coverages)):
            for j in range(len(coverages)):
                eps_ij = epsilon[i*N_ads+j]
                sum_1 += 0.5*eps_ij*f[i]*coverages[i]*f[j]*coverages[j]

        return sum_1

        

    @staticmethod
    def smooth_piecewise_linear_response(*args,**kwargs):
        #Note these need to override first-order functions
        #since second-derivatives are needed
        return smooth_piecewise_linear(*args,**kwargs)

    @staticmethod
    def offset_smooth_piecewise_linear_response(*args,**kwargs):
        return offset_smooth_piecewise_linear(*args,**kwargs)

    @staticmethod
    def piecewise_linear_response(*args,**kwargs):
        kwargs['smoothing'] = 0
        return smooth_piecewise_linear(*args,**kwargs)

    @staticmethod
    def linear_response(*args,**kwargs):
        kwargs['smoothing'] = 0
        kwargs['cutoff'] = 0
        return smooth_piecewise_linear(*args,**kwargs)
