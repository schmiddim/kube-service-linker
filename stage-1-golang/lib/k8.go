package k8

import (
	"fmt"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"log"
)

// Hello ist eine Beispiel-Funktion
func Hello() {
	fmt.Println("Hallo von der util-Funktion!")
}

func HandleAddDeployment(obj interface{}) {
	deployment := obj.(*appsv1.Deployment)
	if MatchLabel("decMgmtProvides", deployment, "deployment") {
		fmt.Printf("Deployment %s in ns %s has label decMgmtProvides\n", deployment.Name, deployment.Namespace)
	}
	fmt.Printf("Deployment %s in ns %s has label decMgmtProvides\n", deployment.Name, deployment.Namespace)

}

func HandleUpdateDeployment(oldObj, newObj interface{}) {
	deployment := newObj.(*appsv1.Deployment)
	//log.Printf("Deployment aktualisiert: %s/%s", deployment.Namespace, deployment.Name)
	if MatchLabel("decMgmtProvides", deployment, "deployment") {
		fmt.Printf("Deployment %s in ns %s has label decMgmtProvides\n", deployment.Name, deployment.Namespace)
	}
	fmt.Printf("Deployment %s in ns %s has label decMgmtProvides\n", deployment.Name, deployment.Namespace)

}

func HandleAddService(obj interface{}) {
	service := obj.(*corev1.Service)

	if MatchLabel("decMgmtProvides", obj, "service") {
		fmt.Printf("Svc %s in ns %s has label decMgmtProvides\n", service.Name, service.Namespace)
	}
	log.Printf("Neuer Service erstellt: %s/%s", service.Namespace, service.Name)
}
func HandleUpdateService(oldObj, newObj interface{}) {
	service := newObj.(*corev1.Service)
	if MatchLabel("decMgmtProvides", newObj, "service") {
		fmt.Printf("Svc %s in ns %s has label decMgmtProvides\n", service.Name, service.Namespace)
	}
	log.Printf("Service aktualisiert: %s/%s", service.Namespace, service.Name)
}

func MatchLabel(name string, service interface{}, crd string) bool {
	//item := service
	//if crd == "service" {
	//	item = service.(*corev1.Service)
	//} else if service == "deployment" {
	//	item = service.(*appsv1.Deployment)
	//} else {
	//	log.Fatal(fmt.Printf("unkown crd %s", crd))
	//}
	//for label, _ := range (item).Labels {
	//	if label == name {
	//		return true
	//
	//		//fmt.Println(label, value)
	//
	//	}
	//}
	return false
}
