from pymoo.core.problem import ElementwiseProblem

import itertools

import numpy as np
from pymoo.core.repair import Repair
from datetime import timedelta

from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
from pymoo.operators.sampling.rnd import PermutationRandomSampling
from pymoo.operators.crossover.ox import OrderCrossover
from pymoo.operators.mutation.inversion import InversionMutation
from pymoo.termination.default import DefaultSingleObjectiveTermination


class TravelingSalesman(ElementwiseProblem):

    def __init__(self, weighted_prices_travel_times, travel_dates, prices, max_total_price, possible_tickets,
                 vars_amount, travel_days, **kwargs):

        self.wptt = weighted_prices_travel_times
        self.prices = prices
        self.max_total_price = max_total_price
        self.travel_dates = travel_dates
        self.travel_days = travel_days

        super(TravelingSalesman, self).__init__(
            n_obj=1,
            n_var=vars_amount,
            n_vars=possible_tickets,
            n_ieq_constr=1,
            n_eq_constr=1,
            vtype=int,
            **kwargs
        )

    def _evaluate(self, x, out, *args, **kwargs):
        out['F'] = self.combined_distances_travel_times(x)
        g1 = self.evaluate_total_price(x) - self.max_total_price
        out["G"] = [g1]
        h1 = self.evaluate_travel_dates(x)
        out["H"] = [h1]

    def evaluate_travel_dates(self, x):
        try:
            n_cities = len(x)
            travel_dates_data = []
            for k in range(n_cities - 1):
                i, j = x[k], x[k + 1]
                travel_dates_data.append(self.travel_dates[i, j].date())

            last, first = x[-1], x[0]
            travel_dates_data.append(self.travel_dates[last, first].date())

            # check for uniqueness
            if len(list(set(travel_dates_data))) == len(travel_dates_data) and 0 not in travel_dates_data:
                for l in range(len(travel_dates_data) - 1):
                    if travel_dates_data[l] < travel_dates_data[l + 1]:
                        continue
                    return -1
                for m in range(len(travel_dates_data) - 1):
                    delta = travel_dates_data[m] + timedelta(days=int(self.travel_days[x[m + 1]]))
                    if delta != travel_dates_data[m + 1]:
                        return -1
                return 0
            return -1
        except Exception:
            return -1

    def evaluate_total_price(self, x):
        n_cities = len(x)
        price = 0
        for k in range(n_cities - 1):
            i, j = x[k], x[k + 1]
            price += self.prices[i, j]

        last, first = x[-1], x[0]
        price += self.prices[last, first]  # back to the initial city
        return price

    def combined_distances_travel_times(self, x):
        n_cities = len(x)
        weighted_prices_total_times = 0
        for k in range(n_cities - 1):
            i, j = x[k], x[k + 1]
            weighted_prices_total_times += self.wptt[i, j]

        last, first = x[-1], x[0]
        weighted_prices_total_times += self.wptt[last, first]  # back to the initial city

        return weighted_prices_total_times


class StartFromZeroRepair(Repair):

    def _do(self, problem, X, **kwargs):
        I = np.where(X == 0)[1]

        for k in range(len(X)):
            i = I[k]
            X[k] = np.concatenate([X[k, i:], X[k, :i]])

        return X


def make_possible_combinations(cities_amount, stay_in_cities, prices_on_diff_dates,
                            travel_times_on_diff_dates, travel_dates_data, ticket_ids):
    combinations_prices, combinations_travel_times,\
    combinations_travel_dates, combinations_tickets = [], [], [], []
    for i in range(cities_amount):
        sub_list_prices, sub_list_travel_times = prices_on_diff_dates[i], travel_times_on_diff_dates[i]
        sub_list_travel_dates, sub_list_ticket_ids = travel_dates_data[i], ticket_ids[i]

        combinations_prices.append(list(itertools.product(*sub_list_prices)))
        combinations_travel_times.append(list(itertools.product(*sub_list_travel_times)))
        combinations_travel_dates.append(list(itertools.product(*sub_list_travel_dates)))
        combinations_tickets.append(list(itertools.product(*sub_list_ticket_ids)))

    return (combinations_prices, combinations_travel_times, combinations_travel_dates,
            combinations_tickets)


def check_unique_dates(datetimes):
    dates = []
    for value in datetimes:
        if value == 0 or value == None:
            dates.append(value)
            continue
        dates.append(value.date())
    return len(dates) == len(set(dates))


def get_filtered_params(specific_dct, filtered_travel_dates_combinations):
    result_lst = []
    for i in range(len(filtered_travel_dates_combinations)):
        tmp_lst = []
        for value in filtered_travel_dates_combinations[i]:
            tmp_lst.append(specific_dct[value])
        result_lst.append(tmp_lst)
    return result_lst


def filter_combinations(combinations_travel_dates, combinations_prices,
                        combinations_travel_times, combinations_tickets):
    prices_dct = dict()
    travel_times_dct = dict()
    travel_tickets_dct = dict()
    for i in range(len(combinations_travel_dates)):
        for k in range(len(combinations_travel_dates[i])):
            prices_dct[combinations_travel_dates[i][k]] = combinations_prices[i][k]
            travel_times_dct[combinations_travel_dates[i][k]] = combinations_travel_times[i][k]
            travel_tickets_dct[combinations_travel_dates[i][k]] = combinations_tickets[i][k]

    filtered_travel_dates_combinations = []
    for i in range(len(combinations_travel_dates)):

        if i == 0:
            filtered_travel_dates_combinations.append(combinations_travel_dates[i])
            continue
        tmp_lst = []
        for value in combinations_travel_dates[i]:
            print(value)
            if check_unique_dates(value):
                tmp_lst.append(value)
        print(tmp_lst)
        print('len tmp_lst: ', len(tmp_lst))
        indx = int(len(tmp_lst)/2)
        print("indx: ", indx)
        if indx > 4:
            indx = 4
            if indx ** len(combinations_travel_dates) >= 256:
                indx = 3
        elif indx < 2:
            indx = len(tmp_lst)
        print("indx trans: ", indx)
        filtered_travel_dates_combinations.append(tuple(tmp_lst[:indx]))

    filtered_prices = get_filtered_params(prices_dct, filtered_travel_dates_combinations)
    filtered_travel_times = get_filtered_params(travel_times_dct, filtered_travel_dates_combinations)
    filtered_tickets = get_filtered_params(travel_tickets_dct, filtered_travel_dates_combinations)

    return (filtered_prices, filtered_travel_times, filtered_travel_dates_combinations,  filtered_tickets)


def make_possible_tsp_tasks(combinations_prices, combinations_travel_times, combinations_travel_dates,
                            combinations_tickets):
    prices = []
    for value in list(itertools.product(*combinations_prices)):
        print(value)
        prices.append(np.array(value))

    travel_times = []
    for value in list(itertools.product(*combinations_travel_times)):
        travel_times.append(np.array(value))

    travel_dates = []
    for value in list(itertools.product(*combinations_travel_dates)):
        travel_dates.append(np.array(value))

    ticket_ids = []
    for value in list(itertools.product(*combinations_tickets)):
        ticket_ids.append(np.array(value))

    return (prices, travel_times, travel_dates, ticket_ids)


def solve_tsp(problems_amount, possible_tickets, prices, travel_times, travel_dates, ticket_ids, n_cities,
              max_total_price, vars_amount, destinations_with_days_in_tsp):
    results_dict = dict()

    for i in range(problems_amount):
        try:
            weighted_distances_travel_times = 0.5 * prices[i] + 0.5 * travel_times[i]
        except Exception:
            continue

        problem = TravelingSalesman(weighted_distances_travel_times, travel_dates[i], prices[i], max_total_price,
                                    possible_tickets, vars_amount, destinations_with_days_in_tsp)

        algorithm = GA(
            pop_size=100,
            sampling=PermutationRandomSampling(),
            mutation=InversionMutation(),
            crossover=OrderCrossover(),
            repair=StartFromZeroRepair(),
            eliminate_duplicates=True
        )
        termination = DefaultSingleObjectiveTermination(period=3, n_max_gen=np.inf)

        res = minimize(
            problem,
            algorithm,
            termination,
            seed=1,
            save_history=True,
            verbose=True
        )

        if res.X is not None:
            result = res.X
            func_result = res.F[0]
            selected_tickets_ids = []

            total_price = 0
            total_duration = 0


            for k in range(n_cities):
                if k == (len(result) - 1):
                    selected_ticket = ticket_ids[i][result[k]][0]
                    total_price += prices[i][result[k]][0]
                    total_duration += travel_times[i][result[k]][0]
                else:
                    selected_ticket = ticket_ids[i][result[k]][result[k + 1]]
                    total_price += prices[i][result[k]][result[k + 1]]
                    total_duration += travel_times[i][result[k]][result[k + 1]]
                selected_tickets_ids.append(selected_ticket)

            results_dict['result' + str(i)] = [list(result), func_result, selected_tickets_ids, round(total_price, 2),
                                               round(total_duration, 2)]

    return results_dict
