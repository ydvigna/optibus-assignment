#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: optibus_assignment.py
Author: Yuri Yasuda
Date: 2024-09-30
Version: 1.0
Description: 
    This contains the solution for the 3 exercises of the home asignment.
        1. Start and End Time
        2. Start and End Stop Name
        3. Breaks
    The script prints the results to standard output in table format.
    A valid JSON dataset file is expected as argument. 
    This code also contains tests to validate the dataset structure and 
    tests for some of the functions. 

Usage: python3 optibus_assignment.py 'mini_json_dataset.json'
Contact: ydvigna@gmail.com
Python Version: 3.9.13
Dependencies: sys, json, pathlib, tabulate, datetime
"""

import sys
import json

from pathlib import Path
from tabulate import tabulate
from datetime import timedelta


def get_vehicle_event(vehicles, vehicle_id, vehicle_event_sequence):
    """Return an event matching vehicle_id and vehicle_event_sequence"""
    try:
        # Generator expression to get first match of vehicle ID and Sequence
        event = next((event for vehicle in vehicles if vehicle['vehicle_id'] == vehicle_id
                            for event in vehicle['vehicle_events']
                            if event['vehicle_event_sequence'] == vehicle_event_sequence), None)
    except Exception as e:
        print(f"{e.args}. vehicle_id:{vehicle_id}, vehicle_event_sequence:{vehicle_event_sequence}")
        return None
    else:
        return event

def get_first_service_trip(duty_events, vehicles):
    """Return the first service_trip event from the duty_events in duty"""
    try:
        # Iterate over duty_events to get a vehicle_event that is service_trip
        for duty_event in duty_events:
            if duty_event['duty_event_type'] == 'vehicle_event':
                event = get_vehicle_event(vehicles,
                                          duty_event['vehicle_id'],
                                          str(duty_event['vehicle_event_sequence']))
                if event == None:
                    return None
                elif event['vehicle_event_type'] == "service_trip":
                    return event
    except Exception as e:
        print(e.args)
        return None
    else:
        # service_trip not found in duty_events
        return None
    
def get_last_service_trip(duty_events, vehicles):
    """Return the last service_trip event from the duty_events in duty"""
    try:
        return get_first_service_trip(reversed(duty_events), vehicles)
    except Exception as e:
        print(e.args)
        return None

def get_start_stop(event, trips, stops):
    """Return the start stop description of the event"""
    try:
        description = next((stop['stop_name'] for trip in trips if trip['trip_id'] == event['trip_id']
                            for stop in stops if stop['stop_id'] == trip["origin_stop_id"]), None)
    except Exception as e:
        print(e.args)
        return None
    else:
        return description
    
def get_end_stop(event, trips, stops):
    """Return the end stop description of the event"""
    try:
        description = next((stop['stop_name'] for trip in trips if trip['trip_id'] == event['trip_id']
                            for stop in stops if stop['stop_id'] == trip["destination_stop_id"]), None)
    except Exception as e:
        print(e.args)
        return None
    else:
        return description
    
def get_stop_name(destination_stop_id, stops):
    """Return the end stop description of the event"""
    try:
        name = next((stop['stop_name'] for stop in stops
                     if stop['stop_id'] == destination_stop_id), None)
    except Exception as e:
        print(e.args)
        return None
    else:
        return name
    
def get_time_difference_minutes(start_time, end_time):
    """Return the difference between two times in minutes"""
    try:
        start_time_split = start_time.replace(':', '.').split('.')
        end_time_split = end_time.replace(':', '.').split('.')
        start_timedelta = timedelta(days=int(start_time_split[0]),
                                    hours=int(start_time_split[1]),
                                    minutes=int(start_time_split[2]))
        end_timedelta = timedelta(days=int(end_time_split[0]),
                                    hours=int(end_time_split[1]),
                                    minutes=int(end_time_split[2]))
        delta = end_timedelta - start_timedelta
    except Exception as e:
        print(e.args)
        return None
    else:
        return delta.total_seconds() / 60
    
def get_event_list(duty_events, stops, vehicles, trips):
    """Return events in the duty_events in a single list"""
    try:
        event_list = []
        # Find time and stop of all events in the duty_events
        for duty_event in duty_events:
            if duty_event['duty_event_type'] in {"sign_on", "taxi"}:
                # All the information needed is in the duty_event
                name = get_stop_name(duty_event['destination_stop_id'], stops)
                event_list.append({
                    'start_time': duty_event['start_time'],
                    'end_time': duty_event['end_time'],
                    'destination_stop_name': name
                })
            elif duty_event['duty_event_type'] == "vehicle_event":
                # Need information from vehicle_events
                vehicle_event = get_vehicle_event(vehicles,
                                                    duty_event['vehicle_id'],
                                                    str(duty_event['vehicle_event_sequence']))
                
                if vehicle_event is None:
                    # Vehicle event not found in dataset, cannot get full event list
                    raise ValueError("Vehicle event not found in dataset, cannot get full event list.")
                
                if vehicle_event['vehicle_event_type'] in {'pre_trip', 'depot_pull_out', 'deadhead',
                                                            'depot_pull_in', 'attendance'}:
                    # All the information needed is in the vehicle_event
                    name = get_stop_name(vehicle_event['destination_stop_id'], stops)
                    event_list.append({
                        'start_time': vehicle_event['start_time'],
                        'end_time': vehicle_event['end_time'],
                        'destination_stop_name': name
                    })
                elif vehicle_event['vehicle_event_type'] == "service_trip":
                    trip = next((trip for trip in trips
                                    if trip['trip_id'] == vehicle_event['trip_id']), None)
                    # All the information needed is in the trip
                    name = get_stop_name(trip['destination_stop_id'], stops)
                    event_list.append({
                        'start_time': trip['departure_time'],
                        'end_time': trip['arrival_time'],
                        'destination_stop_name': name
                    })
                else:
                    raise ValueError("Vehicle event type unknown, cannot get full event list.")
            else:
                raise ValueError("Duty event type unknown, cannot get full event list.")
    except Exception as e:
        print(e.args)
        return []
    else:
        return event_list

def print_times_report(dataset_file):
    """Print report with Duty ID, Start Time, and End Time for duties in dataset."""
    # List of Duty Reports 
    # {Duty ID, Start Time, End Time}
    duty_report = []

    try:
        # Open JSON dataset file
        with open(dataset_file) as f:
            data = json.load(f)

            # Run all duties in the dataset
            for duty in data['duties']:
                start_time = ''
                end_time = ''

                first_duty_event = duty['duty_events'][0]
                last_duty_event = duty['duty_events'][-1]

                first_duty_keys = first_duty_event.keys()

                # Find Start Time of the duty (consider all events)
                if 'start_time' in first_duty_keys:
                    start_time = first_duty_event['start_time']
                elif 'vehicle_id' in first_duty_keys and 'vehicle_event_sequence' in first_duty_keys:
                    vehicle_event = get_vehicle_event(data['vehicles'],
                                                    first_duty_event['vehicle_id'],
                                                    str(first_duty_event['vehicle_event_sequence']))
                    if vehicle_event:
                        start_time = vehicle_event['start_time']

                last_duty_keys = last_duty_event.keys()

                # Find End Time of the duty (consider all events)
                if 'end_time' in last_duty_keys:
                    end_time = last_duty_event['end_time']
                elif 'vehicle_id' in last_duty_keys and 'vehicle_event_sequence' in last_duty_keys:
                    vehicle_event = get_vehicle_event(data['vehicles'],
                                                    last_duty_event['vehicle_id'],
                                                    str(last_duty_event['vehicle_event_sequence']))
                    if vehicle_event:
                        end_time = vehicle_event['end_time']

                duty_report.append({
                    "Duty ID": duty['duty_id'],
                    "Start Time": start_time[2:],
                    "End Time": end_time[2:]
                })
        
        # Print final report formatted as table
        print("--- DUTY TIMES REPORT ---\n")
        print(tabulate(duty_report, headers="keys", stralign="right"))
        print("\n") # empty line
    except Exception as e:
        print(e.args)

def print_stop_names_report(dataset_file):
    """Print report with Duty ID, Start Time, End Time, Start stop description, 
    and End stop description for duties in dataset.
    """
    # List of Duty Reports 
    # {Duty ID, Start Time, End Time, Start stop description, End stop description}
    duty_report = []

    try:
        # Open JSON dataset file
        with open(dataset_file) as f:
            data = json.load(f)

            # Run all duties in the dataset
            for duty in data['duties']:
                start_time = ''
                end_time = ''
                start_stop = ''
                end_stop = ''

                first_duty_event = duty['duty_events'][0]
                last_duty_event = duty['duty_events'][-1]

                first_duty_keys = first_duty_event.keys()

                # Find Start Time of the duty (consider all events)
                if 'start_time' in first_duty_keys:
                    start_time = first_duty_event['start_time']
                elif 'vehicle_id' in first_duty_keys and 'vehicle_event_sequence' in first_duty_keys:
                    vehicle_event = get_vehicle_event(data['vehicles'],
                                                    first_duty_event['vehicle_id'],
                                                    str(first_duty_event['vehicle_event_sequence']))
                    if vehicle_event:
                        start_time = vehicle_event['start_time']

                last_duty_keys = last_duty_event.keys()

                # Find End Time of the duty (consider all events)
                if 'end_time' in last_duty_keys:
                    end_time = last_duty_event['end_time']
                elif 'vehicle_id' in last_duty_keys and 'vehicle_event_sequence' in last_duty_keys:
                    vehicle_event = get_vehicle_event(data['vehicles'],
                                                    last_duty_event['vehicle_id'],
                                                    str(last_duty_event['vehicle_event_sequence']))
                    if vehicle_event:
                        end_time = vehicle_event['end_time']

                # Find Start Stop Description of first service trip
                first_service_trip = get_first_service_trip(
                    duty['duty_events'],
                    data['vehicles']
                )

                start_stop = get_start_stop(
                    first_service_trip,
                    data['trips'],
                    data['stops']
                )

                # Find End Stop Description of last service trip
                last_service_trip = get_last_service_trip(
                    duty['duty_events'],
                    data['vehicles']
                )

                end_stop = get_end_stop(
                    last_service_trip,
                    data['trips'],
                    data['stops']
                )

                duty_report.append({
                    "Duty ID": duty['duty_id'],
                    "Start Time": start_time[2:],
                    "End Time": end_time[2:],
                    "Start Stop Description": start_stop,
                    "End Stop Description": end_stop
                })
        
        # Print final report formatted as table
        print("--- DUTY TIMES AND STOPS REPORT ---\n")
        print(tabulate(duty_report, headers="keys", stralign="right"))
        print("\n") # empty line
    except Exception as e:
        print(e.args)

def print_breaks_report(dataset_file, min_duration):
    """Print report with Duty ID, Start Time, End Time, Start stop description, 
    End stop description, Break start time, Break duration (min), and Break stop name
    for every break over 'min_duration' minutes of all duties in dataset.
    """
    # List of Duty Reports 
    # {Duty ID, Start Time, End Time, Start stop description, End stop description, 
    # Break start time, Break duration, Break stop name}
    duty_report = []

    try:
        # Open JSON dataset file
        with open(dataset_file) as f:
            data = json.load(f)

            # Run all duties in the dataset
            for duty in data['duties']:
                start_time = ''
                end_time = ''
                start_stop = ''
                end_stop = ''

                first_duty_event = duty['duty_events'][0]
                last_duty_event = duty['duty_events'][-1]

                first_duty_keys = first_duty_event.keys()

                # Find Start Time of the duty (consider all events)
                if 'start_time' in first_duty_keys:
                    start_time = first_duty_event['start_time']
                elif 'vehicle_id' in first_duty_keys and 'vehicle_event_sequence' in first_duty_keys:
                    vehicle_event = get_vehicle_event(data['vehicles'],
                                                    first_duty_event['vehicle_id'],
                                                    str(first_duty_event['vehicle_event_sequence']))
                    if vehicle_event:
                        start_time = vehicle_event['start_time']

                last_duty_keys = last_duty_event.keys()

                # Find End Time of the duty (consider all events)
                if 'end_time' in last_duty_keys:
                    end_time = last_duty_event['end_time']
                elif 'vehicle_id' in last_duty_keys and 'vehicle_event_sequence' in last_duty_keys:
                    vehicle_event = get_vehicle_event(data['vehicles'],
                                                    last_duty_event['vehicle_id'],
                                                    str(last_duty_event['vehicle_event_sequence']))
                    if vehicle_event:
                        end_time = vehicle_event['end_time']

                # Find Start Stop Description of first service trip
                first_service_trip = get_first_service_trip(
                    duty['duty_events'],
                    data['vehicles']
                )

                start_stop = get_start_stop(
                    first_service_trip,
                    data['trips'],
                    data['stops']
                )

                # Find End Stop Description of last service trip
                last_service_trip = get_last_service_trip(
                    duty['duty_events'],
                    data['vehicles']
                )

                end_stop = get_end_stop(
                    last_service_trip,
                    data['trips'],
                    data['stops']
                )

                # Get times and stops of all events from the duty_events
                event_list = get_event_list(
                    duty['duty_events'], data['stops'], data['vehicles'], data['trips']
                )
                
                # Find breaks larger thatn 15 minutes between events
                for count, event in enumerate(event_list[:-1]):
                    break_duration = get_time_difference_minutes(
                        event_list[count]['end_time'], event_list[count+1]['start_time']
                    )

                    if break_duration > min_duration:
                        duty_report.append({
                            "Duty ID": duty['duty_id'],
                            "Start Time": start_time[2:],
                            "End Time": end_time[2:],
                            "Start Stop Description": start_stop,
                            "End Stop Description": end_stop, 
                            "Break start time": event_list[count]['end_time'][2:], 
                            "Break duration": break_duration, 
                            "Break stop name": event_list[count]['destination_stop_name']
                        })
        
        # Print final report formatted as table
        print("--- BREAKS REPORT ---\n")
        print(tabulate(duty_report, headers="keys", stralign="right"))
        print("\n") # empty line
    except Exception as e:
        print(e.args)


def test_dataset_structure(dataset_file):
    """Check the dataset structure based on Data Model documentation"""
    # Open JSON dataset file
    with open(dataset_file) as f:
        data = json.load(f)

        assert isinstance(data, dict)

        assert 'stops' in data.keys()
        assert 'trips' in data.keys()
        assert 'vehicles' in data.keys()
        assert 'duties' in data.keys()

        assert isinstance(data['stops'], list)
        assert isinstance(data['trips'], list)
        assert isinstance(data['vehicles'], list)
        assert isinstance(data['duties'], list)

        for stop in data['stops']:
            assert "stop_id" in stop
            assert "stop_name" in stop
            assert "latitude" in stop
            assert "longitude" in stop
            assert "is_depot" in stop

        for trip in data['trips']:
            assert "trip_id" in trip
            assert "route_number" in trip
            assert "origin_stop_id" in trip
            assert "destination_stop_id" in trip
            assert "departure_time" in trip
            assert "arrival_time" in trip

        # TODO: Add similar tests for 'vehicles' and 'duties'

def test_get_vehicle_event(test_vehicles):
    """Tests for get_vehicle_event(), valid and invalid vehicle and sequence"""
    # Positive test: vehicle and event are valid and found
    vehicle_event = get_vehicle_event(test_vehicles, "1", "0")
    assert vehicle_event['vehicle_event_sequence'] == "0"

    # Negative test: vehicle is invalid, event is valid and not found
    vehicle_event = get_vehicle_event(test_vehicles, "0", "0")
    assert vehicle_event == None

    # Negative test: vehicle is valid, event is invalid and not found
    vehicle_event = get_vehicle_event(test_vehicles, "1", "1")
    assert vehicle_event == None

def test_get_first_service_trip(test_vehicles, test_duty_events_positive, test_duty_events_negative):
    """Tests for get_first_service_trip(), valid and invalid duty events"""
    # Positive test: first event found
    first_service_trip = get_first_service_trip(test_duty_events_positive, test_vehicles)
    assert first_service_trip['vehicle_event_sequence'] == "2"

    # Negative test: first event not found
    first_service_trip = get_first_service_trip(test_duty_events_negative, test_vehicles)
    assert first_service_trip == None

def test_get_last_service_trip(test_vehicles, test_duty_events_positive, test_duty_events_negative):
    """Tests for get_last_service_trip(), valid and invalid duty events"""
    # Positive test: last event found
    last_service_trip = get_last_service_trip(test_duty_events_positive, test_vehicles)
    assert last_service_trip['vehicle_event_sequence'] == "5"

    # Negative test: last event not found
    last_service_trip = get_last_service_trip(test_duty_events_negative, test_vehicles)
    assert last_service_trip == None

def test_get_start_stop():
    # TODO: 
    pass

def test_get_end_stop():
    # TODO: 
    pass

def test_get_stop_name():
    # TODO: 
    pass

def test_get_time_difference_minutes():
    # TODO: 
    pass

def test_get_event_list():
    # TODO: 
    pass

def run_tests():
    test_dataset_structure(dataset_file)

    test_duty_events_positive = [
        {
            "duty_event_sequence": "0",
            "duty_event_type": "vehicle_event",
            "vehicle_event_sequence": 2,
            "vehicle_id": "1"
        },
        {
            "duty_event_sequence": "1",
            "duty_event_type": "vehicle_event",
            "vehicle_event_sequence": 5,
            "vehicle_id": "1"
    }]

    test_duty_events_negative = [
        {
            "duty_event_sequence": "0",
            "duty_event_type": "vehicle_event",
            "vehicle_event_sequence": 0,
            "vehicle_id": "1"
        },
        {
            "duty_event_sequence": "1",
            "duty_event_type": "vehicle_event",
            "vehicle_event_sequence": 1,
            "vehicle_id": "1"
    }]

    test_vehicles = [{
        "vehicle_id": "1",
        "vehicle_events": [{
            "vehicle_event_sequence": "0",
            "vehicle_event_type": "pre_trip",
            "start_time": "0.03:15",
            "end_time": "0.03:35",
            "origin_stop_id": "Pomona",
            "destination_stop_id": "Pomona",
            "duty_id": "110"
        }, 
        {
            "vehicle_event_sequence": "2",
            "vehicle_event_type": "service_trip",
            "trip_id": "5301431",
            "duty_id": "110"
        },
        {
            "vehicle_event_sequence": "5",
            "vehicle_event_type": "service_trip",
            "trip_id": "5301533",
            "duty_id": "110"
        }]
    }]

    test_get_vehicle_event(test_vehicles)
    test_get_first_service_trip(test_vehicles, test_duty_events_positive, test_duty_events_negative)
    test_get_last_service_trip(test_vehicles, test_duty_events_positive, test_duty_events_negative)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Number of arguments invalid.")
        print("Usage: python3 optibus_assignment.py mini_json_dataset.json")
        sys.exit()

    print("Running Python script:", sys.argv[0])
    print("JSON file passed:", sys.argv[1])
    print() # empty line

    dataset_file = Path(sys.argv[1])
    assert dataset_file.is_file(), "Invalid dataset file"

    # Call test functions and check results
    run_tests()
    print("All tests passed!\n")

    # Call function 1: Start and End Time
    print_times_report(dataset_file)

    # Call function 2: Start and End Stop Name
    print_stop_names_report(dataset_file)
    
    # Call function 3. Breaks
    print_breaks_report(dataset_file, 15)

    print("--- END OF REPORTS ---\n")
