## Architecture

### Main Components

#### 1. **API Gateway**
- **URL**: `base_url`
- **Endpoints**:
  - `/students/schooling` - Upload academic data  
  - `/students/{student_id}/{degree_id}/schooling` - Retrieve student data  
  - `/university/{degree_id}` - Degree information  
  - `/university/subjects` - List of subjects  
  - `/students/{student_id}/{degree_id}/plan` - Study plan  
  - `/recommenders/train` - Train models  
  - `/recommenders/predict` - Make predictions  
  - `/recommenders/asb` - ASB recommendations  

#### 2. **Lambda Functions**
- **UploadSchoolingFunction** - Upload academic data  
- **GetSchoolingFunction** - Retrieve student data  
- **GetDegreePathFunction** - Degree information  
- **GetSubjectsFunction** - Subject management  
- **GetStudentPlanFunction** - Study plans  
- **SageMakerTrainFunction** - Model training  
- **SageMakerPredictFunction** - Predictions  
- **ASBRecommenderDockerFunction** - ASB recommendations  

#### 3. **SageMaker Endpoints**
- **PM Endpoint** - Process Mining  
- **RF Endpoint** - Random Forest  
- **SPM Endpoint** - Sequential Pattern Mining  

## Recommendation Algorithms

### 1. **Process Mining (PM)**
- **Endpoint**: `pm-endpoint`  
- **Description**: Analyzes student behavioral patterns  
- **Parameters**:  
  - `GPA_SUCCESS_THRESHOLD`: 3.6  
  - `SIMILARITY_THRESHOLD`: 0.7  
  - `TOP_K`: 5  

### 2. **Random Forest (RF)**
- **Endpoint**: `rf-endpoint`  
- **Description**: Classification based on decision trees  
- **Parameters**:  
  - `n_estimators`: 400  
  - `max_depth`: 10  
  - `random_state`: 123  

### 3. **Sequential Pattern Mining (SPM)**
- **Endpoint**: `spm-endpoint`  
- **Description**: Discovers sequential patterns in performance  
- **Parameters**:  
  - `MIN_SUPPORT`: 0.20  
  - `MAX_PATTERN_LENGTH`: 6  
  - `TOP_K`: 4  

### 4. **Academic Success Behavior (ASB)**
- **Lambda Function**: ASBRecommenderDockerFunction  
- **Description**: Academic behavior analysis  
- **Configurable Parameters**:  
  - `feature`: Course-Semester, Course-Order, etc.  
  - `is_atomic`: true/false  
  - `index_type`: fachsemester, order, distance  
  - `label`: Overall GPA, Course grade, Pass/Fail  

### S3 Bucket
- **Bucket**: `recommendation-data`  
- **Structure**:  
```text
s3://recommendation-data/
├── recommenders/
│   └── models/
│       ├── pm/
│       │   └── {degree_id}/
│       ├── rf/
│       │   └── {degree_id}/
│       └── spm/
│           └── {degree_id}/
└── student-activity/
    └── {activity files}
  ```

## Development

### Project Structure
```
backend/
├── src/
│   ├── handler/          # Lambda functions
│   ├── model/            # Data models
│   ├── repository/       # Data access
│   ├── services/         # Business logic
│   └── support/          # Utilities
├── sagemaker/
│   ├── recommender/      # Training scripts and algorithms
│   └── Dockerfile        # SageMaker image
├── template.yml          # CloudFormation infrastructure
└── requirements.txt      # Python dependencies

### Adding a New Algorithm
1. Create a training script under `src/recommender/`  
2. Update the `Dockerfile` to include the script  
3. Modify `sagemaker_train_handler.py` to support the new algorithm  
4. Update training scripts accordingly  
