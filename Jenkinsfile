pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    git branch: 'main', credentialsId: 'be931eed-297a-4c57-9706-565d76161ee0', url: 'https://github.com/WitesoAI/Witeso'
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    sh 'sudo apt install python3-pip -y && pip3 install virtualenv'
                    sh '''
                    chmod +x envsetup.sh
                    ./envsetup.sh
                    '''
                }
            }
        }

        stage('Configure Ngnix') {
            steps {
                script {
                    sh 'sudo cp -rf DevOps/witeso.conf /etc/nginx/sites-available/witeso'
                    try {
                        sh 'sudo rm /etc/nginx/sites-enabled/witeso'
                    } catch (Exception e) {
                        echo "Nginx Config does'nt exist: ${e.message}"
                    }
                    sh 'sudo ln -s /etc/nginx/sites-available/witeso /etc/nginx/sites-enabled'
                    sh 'sudo nginx -t'
                    sh 'sudo systemctl reload nginx'
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sh 'sudo cp -rf DevOps/gunicorn_witeso.service /etc/systemd/system/'
                    sh 'sudo systemctl daemon-reload'

                    sh 'sudo systemctl start gunicorn_witeso.service'
                    sh 'echo "Gunicorn has started."'

                    sh 'sudo systemctl enable gunicorn_witeso.service'
                    sh 'echo "Gunicorn has been enabled."'

                    sh 'sudo systemctl status gunicorn_witeso.service'
                    sh 'sudo systemctl restart gunicorn_witeso.service'
                }
            }
        }
    }

    post {
        success {
            echo 'Deployment successful!'
        }
    }
}