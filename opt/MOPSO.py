# Multi-Objective Particle Swarm Optimization (MOPSO) class
# modifying the MOPSO from jMetal.py pachage for
# PowerSynth to support Hierarchical structure

import random

from typing import Generic, List, TypeVar, Optional
from jmetal.core.problem import Problem
from jmetal.core.problem import FloatProblem
from jmetal.algorithm.multiobjective.omopso import OMOPSO
from jmetal.core.solution import (
    BinarySolution,
    FloatSolution,
    IntegerSolution,
    PermutationSolution,
    )
from jmetal.operator import UniformMutation
from jmetal.operator.mutation import NonUniformMutation
from jmetal.util.archive import BoundedArchive, NonDominatedSolutionsArchive
from jmetal.util.termination_criterion import TerminationCriterion
from jmetal.config import store
from jmetal.util.evaluator import Evaluator
from jmetal.util.generator import Generator
     
# modify the create solutiom method in FloatProblem class
class FloatProblemMOPSO(FloatProblem):
    def create_solution(self) -> FloatSolution:
        new_solution = FloatSolution(
            self.lower_bound, self.upper_bound, self.number_of_objectives(), self.number_of_constraints()
        )
        new_solution.variables = [
            random.uniform(self.lower_bound[i] * 1.0, self.upper_bound[i] * 1.0)
            for i in range(self.number_of_variables())
        ]
        i = 0
        j = 0
        
        if self.sub_vars[-1] == 1:
            self.sub_vars[-1] = 2
            for k in self.sub_vars[:-1]:
                j += k
                new_sol =  new_solution.variables[i:j]
                for ii in range(k):
                    new_sol[ii] = new_sol[ii]/sum(new_solution.variables[i:j])
                new_solution.variables[i:j] = new_sol
                i = j
        else:
            for k in self.sub_vars:
                j += k
                new_sol =  new_solution.variables[i:j]
                for ii in range(k):
                    new_sol[ii] = new_sol[ii]/sum(new_solution.variables[i:j])
                new_solution.variables[i:j] = new_sol
                i = j
        
        return new_solution


# add a propertie (sub_vars) to OMOPSO class
# modify the update position method in OMOPSO class    
class MOPSO(OMOPSO):
    def __init__(
        self,
        problem: FloatProblem,
        swarm_size: int,
        uniform_mutation: UniformMutation,
        non_uniform_mutation: NonUniformMutation,
        leaders: Optional[BoundedArchive],
        epsilon: float,
        termination_criterion: TerminationCriterion,
        swarm_generator: Generator = store.default_generator,
        swarm_evaluator: Evaluator = store.default_evaluator,
        sub_vars: List[int] = []
    ):
        super().__init__(problem, swarm_size, uniform_mutation, non_uniform_mutation, leaders, epsilon, termination_criterion)
        self.sub_vars: List[int] = []
        
    def update_position(self, swarm: List[FloatSolution]) -> None:
        for i in range(self.swarm_size):
            particle = swarm[i]

            for j in range(particle.number_of_variables):
                particle.variables[j] += self.speed[i][j]

                if particle.variables[j] < self.problem.lower_bound[j]:
                    particle.variables[j] = self.problem.lower_bound[j]
                    self.speed[i][j] *= self.change_velocity1

                if particle.variables[j] > self.problem.upper_bound[j]:
                    particle.variables[j] = self.problem.upper_bound[j]
                    self.speed[i][j] *= self.change_velocity2

            m = 0
            n = 0
            if self.problem.sub_vars[-1] == 1:
                self.sub_vars[-1] = 2
                for k in self.problrm.sub_vars[:-1]:
                    n += k
                    new_sol =  particle.variables[m:n]
                    for ii in range(k):
                        sum_sub_par = sum(particle.variables[m:n])
                        if sum_sub_par==0:
                            sum_sub_par=1
                        new_sol[ii] = new_sol[ii]/sum_sub_par
                    particle.variables[m:n] = new_sol
                    m = n
            else:
                for k in self.problem.sub_vars:
                    n += k
                    new_sol =  particle.variables[m:n]
                    for ii in range(k):
                        sum_sub_par = sum(particle.variables[m:n])
                        if sum_sub_par==0:
                            sum_sub_par=1
                        new_sol[ii] = new_sol[ii]/sum_sub_par
                    particle.variables[m:n] = new_sol
                    m = n
