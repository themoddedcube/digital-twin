# Requirements Document

## Introduction

The **F1 Dual Digital Twin System (Race Twin Edge)** is a real-time race strategy simulation platform that maintains synchronized digital representations of a racing team’s car and the competitive field.  
The system ingests live telemetry data to update the **Car Twin** (a high-fidelity model of our car’s state) and the **Field Twin** (a behavioral model of competitor cars).  
By continuously updating these twins, the platform enables data-driven strategic decision-making and provides standardized outputs for downstream **simulation** and **AI strategy** systems.

---

## Glossary

- **Car Twin:** A real-time digital model representing our car’s dynamic state based on live telemetry inputs.  
- **Field Twin:** A behavioral simulation model representing competitor cars and their strategic patterns.  
- **Telemetry Ingestor:** Component responsible for collecting, validating, and normalizing live telemetry data.  
- **State Handler:** Component that manages shared environment data (track, weather, flags) and ensures persistence and consistency.  
- **Simulation Engine:** External module that consumes structured twin data for running strategy and performance simulations.  
- **AI Strategist:** External system that analyzes twin data and provides human-readable strategy recommendations.  
- **Telemetry Data:** Real-time or simulated data including speed, tire wear, fuel levels, lap times, track temperature, and weather conditions.

---

## Requirements

### Requirement 1 – Telemetry Ingestion

**User Story:**  
As a race strategist, I want continuous telemetry data ingestion so that the digital twins accurately reflect live race conditions.

**Acceptance Criteria:**
1. WHEN telemetry data is received, the **Telemetry_Ingestor** SHALL normalize it into standardized JSON format within **250 milliseconds**.  
2. The **Telemetry_Ingestor** SHALL update local storage with normalized telemetry data every **3 seconds**.  
3. The **Telemetry_Ingestor** SHALL validate data completeness and schema conformity before processing.  
4. The **Telemetry_Ingestor** SHALL handle missing or corrupted telemetry by maintaining the last valid state.  
5. The **Telemetry_Ingestor** SHALL output the current telemetry state to `/shared/telemetry_state.json`.

---

### Requirement 2 – Car Twin

**User Story:**  
As a race engineer, I want a Car Twin that mirrors our car’s current state so that I can make accurate, data-driven strategy decisions.

**Acceptance Criteria:**
1. WHEN telemetry data updates, the **Car_Twin** SHALL recalculate car state parameters within **200 milliseconds** of receiving the update.  
2. The **Car_Twin** SHALL maintain and update metrics including speed, tire temperature, tire wear, fuel level, and lap time.  
3. The **Car_Twin** SHALL predict tire degradation trends using recent wear and track condition data.  
4. The **Car_Twin** SHALL estimate remaining fuel and projected fuel consumption per lap.  
5. The **Car_Twin** SHALL expose derived metrics such as predicted pit window and lap-time delta.  
6. The **Car_Twin** SHALL output car state data in JSON format for consumption by external systems.

---

### Requirement 3 – Field Twin

**User Story:**  
As a strategist, I want a Field Twin that models competitor behavior so that I can anticipate rival strategies and adjust ours accordingly.

**Acceptance Criteria:**
1. WHEN competitor telemetry or estimated timing data is available, the **Field_Twin** SHALL update competitor models within **300 milliseconds**.  
2. The **Field_Twin** SHALL maintain behavioral models for each competitor, including tire state, pit history, and performance deltas.  
3. The **Field_Twin** SHALL track competitor pit-stop patterns and strategic tendencies (e.g., undercut, overcut likelihood).  
4. The **Field_Twin** SHALL predict competitor lap times based on degradation models and tire choices.  
5. The **Field_Twin** SHALL trigger re-simulations when significant race events occur (e.g., competitor pit, safety car deployment).  
6. The **Field_Twin** SHALL identify strategic opportunities based on competitor positioning, gaps, and degradation levels.

---

### Requirement 4 – State Management

**User Story:**  
As a system administrator, I want robust state management so that the system maintains data integrity under race conditions and recovers reliably.

**Acceptance Criteria:**
1. The **State_Handler** SHALL persist all twin states to local storage every **5 seconds**.  
2. The **State_Handler** SHALL recover from interruptions by loading the most recent valid state.  
3. The **State_Handler** SHALL maintain data consistency between the Car_Twin and Field_Twin models.  
4. The **State_Handler** SHALL perform atomic writes and use concurrency-safe locking mechanisms during updates.  
5. The **State_Handler** SHALL log all state changes with timestamps for audit and replay purposes.

---

### Requirement 5 – Data Outputs and Integration

**User Story:**  
As an integration developer, I want standardized and performant data outputs so that external systems (Simulation Engine, AI Strategist) can consume twin data effectively.

**Acceptance Criteria:**
1. The System SHALL provide REST endpoints for real-time access to twin and environment data.  
2. The System SHALL output structured JSON conforming to predefined schemas with version metadata.  
3. The System SHALL maintain API response times under **50 milliseconds** on local network access.  
4. The System SHALL support concurrent read access by multiple external clients without performance degradation.  
5. The System SHALL maintain backward-compatible data formats through schema versioning.

---

## Summary

The **F1 Dual Digital Twin System** establishes a reliable, modular architecture for real-time race-state modeling and strategy support.  
It ensures:  
- Continuous telemetry synchronization,  
- High-fidelity Car Twin modeling,  
- Behavioral Field Twin predictions,  
- Consistent state persistence, and  
- Standardized, low-latency data outputs for simulation and AI strategy modules.  

These requirements collectively enable a **dual-twin, event-triggered architecture** that serves as the foundation for dynamic HPC simulation and real-time strategic decision-making in Formula 1.
