// Jenkinsfile: CI/CD pipeline with SonarQube, Trivy, Docker Hub and SSH deployment.
pipeline {
    agent any                                              // run on the Jenkins server

    environment {
        DOCKERHUB_USER = 'zeeshan2007'                     // Docker Hub username
        APP_SERVER     = 'APP_SERVER_PRIVATE_IP'           // set to the app server's PRIVATE IP
        IMAGE_NAME     = "${DOCKERHUB_USER}/docker-webapp" // image name on Docker Hub
        IMAGE_TAG      = "${env.BUILD_NUMBER}"             // version = build number
    }

    options {
        timestamps()                                       // time on every log line
        buildDiscarder(logRotator(numToKeepStr: '10'))     // keep the last 10 builds
        disableConcurrentBuilds()                          // one build at a time
        timeout(time: 30, unit: 'MINUTES')                 // stop stuck builds
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }                         // get the code from GitHub
        }

        stage('Unit Tests') {                              // run the developer's tests
            steps {
                dir('app') {
                    sh '''
                        python3 -m venv ../.venv
                        . ../.venv/bin/activate
                        pip install -q -r requirements.txt -r requirements-dev.txt
                        pytest -v --junitxml=../test-results.xml
                    '''
                }
            }
            post { always { junit 'test-results.xml' } }   // show results in Jenkins
        }

        stage('SonarQube Analysis') {                      // send code to SonarQube
            environment { SCANNER_HOME = tool 'sonar-scanner' }
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh '''
                        $SCANNER_HOME/bin/sonar-scanner \
                          -Dsonar.projectKey=docker-webapp \
                          -Dsonar.sources=app \
                          -Dsonar.exclusions=app/test_*.py \
                          -Dsonar.tests=app \
                          -Dsonar.test.inclusions=app/test_*.py \
                          -Dsonar.python.version=3.12
                    '''
                }
            }
        }

        stage('Quality Gate') {                            // STOP if quality is too low
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Trivy: Libraries') {                        // report vulnerable libraries
            steps { sh 'trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 0 app' }
        }

        stage('Build Image') {                             // package the app
            steps { sh 'docker build --build-arg APP_VERSION=${IMAGE_TAG} -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest app' }
        }

        stage('Trivy: Image') {                            // STOP on critical vulnerabilities
            steps { sh 'trivy image --severity CRITICAL --ignore-unfixed --exit-code 1 ${IMAGE_NAME}:${IMAGE_TAG}' }
        }

        stage('Push to Docker Hub') {                      // publish the image
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                 usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN')]) {
                    sh '''
                        echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
                        docker push ${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${IMAGE_NAME}:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to App Server') {                    // SSH to the app server, run the new version
            steps {
                sshagent(credentials: ['app-server-ssh']) {
                    sh '''
                        SSH="ssh -o StrictHostKeyChecking=no ubuntu@${APP_SERVER}"
                        $SSH "mkdir -p ~/app/nginx ~/app/app"
                        scp -o StrictHostKeyChecking=no docker-compose.yml ubuntu@${APP_SERVER}:~/app/
                        scp -o StrictHostKeyChecking=no nginx/default.conf ubuntu@${APP_SERVER}:~/app/nginx/
                        $SSH "cd ~/app && export WEB_IMAGE=${IMAGE_NAME}:${IMAGE_TAG} && docker compose pull && docker compose up -d --no-build --remove-orphans"
                    '''
                }
            }
        }

        stage('Smoke Test') {                              // check the live app answers
            steps {
                sh '''
                    for i in $(seq 1 30); do
                      curl -sf http://${APP_SERVER}/health && echo " ✅ healthy" && exit 0
                      sleep 2
                    done
                    echo "❌ app not healthy"; exit 1
                '''
            }
        }
    }

    post {
        success { echo "✅ Version ${IMAGE_TAG} is live" }
        failure { echo "❌ Build failed. Open the red stage." }
        always  { sh 'docker image prune -f' }             // clean old images on Jenkins
    }
}
