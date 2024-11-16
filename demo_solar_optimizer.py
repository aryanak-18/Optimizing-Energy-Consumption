from datetime import datetime, time
import json
from typing import Dict, List, Optional
import random
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import pandas as pd
from solar_optimizer import SolarSystem
from solar_optimizer import TariffSchedule
from solar_optimizer import EnergyOptimizer
from solar_optimizer import EnergyMonitor

def run_demo():
    print("Initializing Solar Energy Optimization System...")
    solar_capacity = 10.0
    solar_system = SolarSystem(capacity_kw=solar_capacity)
    tariff_schedule = TariffSchedule()
    optimizer = EnergyOptimizer(solar_system, tariff_schedule)
    monitor = EnergyMonitor()

    print("\nAdding household appliances...")
    appliances = {
        "Washing Machine": 1.2,
        "Dishwasher": 1.5,
        "Pool Pump": 1.0,
        "EV Charger": 7.0,
        "Air Conditioner": 2.5,
        "Refrigerator": 0.15,
        "Water Heater": 4.0
    }

    for name, power in appliances.items():
        flexible = name not in ["Refrigerator"]
        optimizer.add_appliance(name, power, flexible)
        print(f"Added {name}: {power}kW {'(Flexible)' if flexible else '(Non-flexible)'}")

    print("\nGenerating optimized schedule...")
    schedule = optimizer.optimize_schedule(24)

    print("\nSimulating 24-hour operation...")
    hourly_data = []
    current_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    for hour in range(24):
        time_slot = current_time.replace(hour=hour)
        generation = solar_system.update_generation(time_slot)
        rate = tariff_schedule.get_current_rate()
        

        scheduled_appliances = schedule.get(hour, [])
        total_usage = sum(optimizer.appliance_schedule[app]['power_usage'] 
                         for app in scheduled_appliances)
        
        grid_usage = max(0, total_usage - generation)
        solar_used = min(total_usage, generation)
        solar_excess = max(0, generation - total_usage)
        cost = grid_usage * rate
        

        monitor.record_usage(time_slot, total_usage, cost)
        
        hourly_data.append({
            'hour': hour,
            'time': time_slot,
            'solar_generation': generation,
            'total_usage': total_usage,
            'grid_usage': grid_usage,
            'solar_used': solar_used,
            'solar_excess': solar_excess,
            'rate': rate,
            'cost': cost,
            'scheduled_appliances': scheduled_appliances
        })

    df = pd.DataFrame(hourly_data)
    

    print("\nDaily Summary:")
    print(f"Total Solar Generation: {df['solar_generation'].sum():.2f} kWh")
    print(f"Total Energy Usage: {df['total_usage'].sum():.2f} kWh")
    print(f"Grid Energy Used: {df['grid_usage'].sum():.2f} kWh")
    print(f"Solar Energy Used: {df['solar_used'].sum():.2f} kWh")
    print(f"Total Cost: ${df['cost'].sum():.2f}")
    

    plt.figure(figsize=(15, 10))
    

    plt.subplot(2, 1, 1)
    plt.plot(df['hour'], df['solar_generation'], 'y-', label='Solar Generation')
    plt.plot(df['hour'], df['total_usage'], 'b-', label='Total Usage')
    plt.plot(df['hour'], df['grid_usage'], 'r-', label='Grid Usage')
    plt.title('24-Hour Energy Flow')
    plt.xlabel('Hour of Day')
    plt.ylabel('Energy (kW)')
    plt.legend()
    plt.grid(True)


    plt.subplot(2, 1, 2)
    plt.bar(df['hour'], df['cost'], color='purple', alpha=0.6)
    plt.title('Hourly Energy Costs')
    plt.xlabel('Hour of Day')
    plt.ylabel('Cost ($)')
    plt.grid(True)

    plt.tight_layout()
    plt.show()

    print("\nOptimized Appliance Schedule:")
    for hour in range(24):
        if hour in schedule and schedule[hour]:
            print(f"{hour:02d}:00 - Running: {', '.join(schedule[hour])}")

if __name__ == "__main__":
    run_demo()