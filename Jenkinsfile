// Pipeline CI declarativo: Checkout → Test → Build → Push (guía avance-semana-2, pasos 11–14)
pipeline {
    agent any

    environment {
        IMAGE_NAME = "grukhoof/devops-taskapi"     // Docker ID en Docker Hub
    }

    triggers {
        pollSCM('H/5 * * * *')                     // SCM polling cada ~5 min (H reparte la carga)
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm                       // clona la rama configurada en el job
            }
        }

        stage('Test') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet -r requirements.txt
                    pytest tests/ -v --junit-xml=test-report.xml
                '''
            }
            post {
                always {
                    junit 'test-report.xml'        // publica el reporte aunque el stage falle
                }
            }
        }

        stage('Build') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} ."
                sh "docker tag ${IMAGE_NAME}:${BUILD_NUMBER} ${IMAGE_NAME}:latest"
            }
        }

        stage('Push') {
            steps {
                // Credenciales inyectadas en memoria; Jenkins las enmascara en los logs
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DOCKER_USER',
                                                  passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${IMAGE_NAME}:${BUILD_NUMBER}
                        docker push ${IMAGE_NAME}:latest
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker logout || true'             // cerrar sesión siempre
            cleanWs()                              // limpiar el workspace
        }
        success {
            echo "Pipeline OK — imagen ${IMAGE_NAME}:${BUILD_NUMBER} publicada en Docker Hub"
        }
        failure {
            echo "Pipeline FAILED en build #${BUILD_NUMBER} — revisar logs"
        }
    }
}
