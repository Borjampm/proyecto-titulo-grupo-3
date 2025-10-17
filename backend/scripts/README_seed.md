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

### Notes

- All data is randomly generated but realistic for a Chilean healthcare context
- The script respects foreign key relationships between models
- Use `--reset` flag to start with a clean database
- The script is safe to run multiple times (will add more data)
