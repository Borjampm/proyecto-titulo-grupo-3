# Database Seeding Script

This directory contains scripts for database management and seeding.

## seed.py

The `seed.py` script populates the database with sample data for development and testing purposes.

### Features

- Creates sample patients with realistic Chilean names and data
- Creates hospital beds with different availability states
- Creates clinical episodes with proper relationships to patients and beds
- Creates patient and episode documents
- Creates clinical episode information records (diagnosis, medications, vital signs, etc.)
- Creates tasks with realistic status progressions and complete audit history

### Usage

#### Basic seeding
```bash
python scripts/seed.py
```

#### Reset database and seed
```bash
python scripts/seed.py --reset
```

### Sample Data Created

#### Patients (4 patients)
- María González (P001) - 39 years old, female
- Carlos Rodríguez (P002) - 46 years old, male
- Ana López (P003) - 32 years old, female
- Diego Martínez (P004) - 59 years old, male

Each patient includes:
- Basic information (name, RUT, birth date, gender)
- Contact information and medical history
- Random patient documents (medical reports, lab results, etc.)

#### Beds (8 beds)
- Regular rooms: 101, 102, 103, 201, 202, 203
- ICU rooms: ICU-1, ICU-2
- Mix of active/available states

#### Clinical Episodes
- 1-2 episodes per patient
- Different statuses (active, discharged, transferred)
- Proper bed assignments
- Episode documents and information records

#### Tasks with Status History (10 administrative tasks for main episode)
1. **Contact Family Member** - Full progression: Pending → In Progress → Completed
2. **Verify Insurance Coverage** - Full progression: Pending → In Progress → Completed
3. **Obtain Consent Form** - Full progression: Pending → In Progress → Completed
4. **Social Work Evaluation** - Full progression: Pending → In Progress → Completed
5. **Verify Outstanding Payments** - Currently in progress: Pending → In Progress
6. **Room Assignment Confirmation** - Still pending
7. **Request Medical Records Transfer** - Cancelled (patient brought records)
8. **Schedule Post-Discharge Follow-up** - Currently in progress
9. **Complete Admission Paperwork** - Full progression: Pending → In Progress → Completed
10. **Dietary Restrictions Update** - Full progression: Pending → In Progress → Completed

All tasks are administrative/procedural (not medical) such as:
- Family communication
- Insurance and billing verification
- Document signing and consent forms
- Social services coordination
- Administrative paperwork

Each task includes:
- Complete status change history with timestamps
- Who made each change (changed_by)
- Notes explaining the change
- Realistic time progression (minutes to hours between status changes)

#### Documents and Information
- Patient documents (medical reports, lab results, imaging, prescriptions)
- Episode documents (admission reports, treatment plans, nursing notes)
- Clinical information (diagnosis, medications, vital signs, etc.)

### Database Models Covered

The script creates data for all models:
- `Patient` - Patient basic information
- `PatientInformation` - Extended patient data (JSONB)
- `PatientDocument` - Documents associated with patients
- `Bed` - Hospital bed management
- `ClinicalEpisode` - Patient hospital stays
- `EpisodeDocument` - Documents for specific episodes
- `ClinicalEpisodeInformation` - Episode-specific information records
- `TaskInstance` - Tasks assigned to episodes
- `TaskStatusHistory` - Complete audit trail of all task status changes

### Notes

- All data is randomly generated but realistic for a Chilean healthcare context
- The script respects foreign key relationships between models
- Use `--reset` flag to start with a clean database
- The script is safe to run multiple times (will add more data)
