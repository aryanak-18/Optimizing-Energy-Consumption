from datetime import datetime, time
import json
from typing import Dict, List, Optional
import random

class TariffSchedule:
    def __init__(self):
        self.periods = {
            'peak': {'start': time(14, 0), 'end': time(20, 0), 'rate': 0.40},
            'shoulder': {'start': time(7, 0), 'end': time(14, 0), 'rate': 0.25},
            'off_peak': {'start': time(20, 0), 'end': time(7, 0), 'rate': 0.15}
        }
    
    def get_current_rate(self) -> float:
        current_time = datetime.now().time()
        
        for period, details in self.periods.items():
            start = details['start']
            end = details['end']

            if end < start:
                if current_time >= start or current_time < end:
                    return details['rate']
            else:
                if start <= current_time < end:
                    return details['rate']
        
        return self.periods['off_peak']['rate']

class SolarSystem:
    def __init__(self, capacity_kw: float):
        self.capacity_kw = capacity_kw
        self.current_generation = 0
        self.stored_energy = 0
        self.max_storage = capacity_kw * 4

    def update_generation(self, time_of_day: datetime) -> float:
        hour = time_of_day.hour
        if 6 <= hour <= 18:
            self.current_generation = self.capacity_kw * (1 - abs(hour - 12) / 6) * random.uniform(0.8, 1.0)
        else:
            self.current_generation = 0
        return self.current_generation

    def store_energy(self, amount: float) -> float:
        available_storage = self.max_storage - self.stored_energy
        amount_to_store = min(amount, available_storage)
        self.stored_energy += amount_to_store
        return amount_to_store

    def use_stored_energy(self, amount: float) -> float:
        amount_to_use = min(amount, self.stored_energy)
        self.stored_energy -= amount_to_use
        return amount_to_use

class EnergyOptimizer:
    def __init__(self, solar_system: SolarSystem, tariff_schedule: TariffSchedule):
        self.solar_system = solar_system
        self.tariff_schedule = tariff_schedule
        self.appliance_schedule: Dict[str, List[Dict]] = {}
        
    def add_appliance(self, name: str, power_usage: float, flexible_timing: bool):
        self.appliance_schedule[name] = {
            'power_usage': power_usage,
            'flexible_timing': flexible_timing,
            'scheduled_runs': []
        }

    def optimize_schedule(self, forecast_window_hours: int = 24) -> Dict:
        schedule = {}
        current_time = datetime.now()
        
        for hour in range(forecast_window_hours):
            time_slot = current_time.replace(hour=hour)
            rate = self.tariff_schedule.get_current_rate()
            solar_generation = self.solar_system.update_generation(time_slot)

            for appliance, details in self.appliance_schedule.items():
                if details['flexible_timing']:
                    if solar_generation > details['power_usage'] or rate == self.tariff_schedule.periods['off_peak']['rate']:
                        if hour not in schedule:
                            schedule[hour] = []
                        schedule[hour].append(appliance)
        
        return schedule

class EnergyMonitor:
    def __init__(self):
        self.usage_history = []
        self.cost_history = []

    def record_usage(self, timestamp: datetime, usage: float, cost: float):
        self.usage_history.append({'timestamp': timestamp, 'usage': usage})
        self.cost_history.append({'timestamp': timestamp, 'cost': cost})

    def get_daily_summary(self) -> Dict:
        if not self.usage_history:
            return {'total_usage': 0, 'total_cost': 0, 'average_rate': 0}

        daily_usage = sum(record['usage'] for record in self.usage_history[-24:])
        daily_cost = sum(record['cost'] for record in self.cost_history[-24:])
        
        return {
            'total_usage': daily_usage,
            'total_cost': daily_cost,
            'average_rate': daily_cost / daily_usage if daily_usage > 0 else 0
        }

def main():
    solar_system = SolarSystem(capacity_kw=10.0)
    tariff_schedule = TariffSchedule()
    optimizer = EnergyOptimizer(solar_system, tariff_schedule)
    monitor = EnergyMonitor()
    

    optimizer.add_appliance("Washing Machine", 1.2, True)
    optimizer.add_appliance("Dishwasher", 1.5, True)
    optimizer.add_appliance("Pool Pump", 1.0, True)
    optimizer.add_appliance("Refrigerator", 0.15, False)

    schedule = optimizer.optimize_schedule()

    current_time = datetime.now()
    for hour in range(24):
        time_slot = current_time.replace(hour=hour)

        generation = solar_system.update_generation(time_slot)
        rate = tariff_schedule.get_current_rate()

        scheduled_appliances = schedule.get(hour, [])
        total_usage = sum(optimizer.appliance_schedule[app]['power_usage'] 
                         for app in scheduled_appliances)
        

        grid_usage = max(0, total_usage - generation)
        cost = grid_usage * rate

        monitor.record_usage(time_slot, total_usage, cost)
    
    summary = monitor.get_daily_summary()
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()