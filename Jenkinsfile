// Pipeline CI/CD declarativo: Checkout → Test → Build → Push → Deploy (guías avance-semana-2 y avance-semana-3)
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

        stage('Deploy') {
            steps {
                // Jenkins corre en un contenedor: 127.0.0.1 / kubernetes.docker.internal no llegan
                // al API server del host, por eso se copia y parchea el kubeconfig (paso 21)
                sh """
                    cp \$HOME/.kube/config /tmp/kubeconfig
                    sed -i 's/127.0.0.1/host.docker.internal/g; s/kubernetes.docker.internal/host.docker.internal/g' /tmp/kubeconfig
                    sed -i 's/certificate-authority-data:.*/insecure-skip-tls-verify: true/' /tmp/kubeconfig
                    export KUBECONFIG=/tmp/kubeconfig

                    kubectl apply -f k8s/namespace.yaml --validate=false
                    kubectl apply -f k8s/ --validate=false

                    # Imagen exacta de este build (trazabilidad) y espera del rollout sin downtime
                    kubectl set image deployment/taskapi taskapi=${IMAGE_NAME}:${BUILD_NUMBER} -n devops-project
                    kubectl rollout status deployment/taskapi -n devops-project --timeout=120s
                """
            }
            post {
                always {
                    sh 'rm -f /tmp/kubeconfig'      // no dejar el kubeconfig parcheado en el contenedor
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
            echo "Pipeline OK — imagen ${IMAGE_NAME}:${BUILD_NUMBER} publicada y desplegada en Kubernetes"
        }
        failure {
            echo "Pipeline FAILED en build #${BUILD_NUMBER} — revisar logs"
        }
    }
}
