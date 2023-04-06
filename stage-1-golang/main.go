package main

import (
	"fmt"
	"os"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/tools/clientcmd"
)

func main() {
	kubeconfig := os.Getenv("KUBECONFIG")
	if kubeconfig == "" {
		kubeconfig = os.Getenv("HOME") + "/.kube/config"
	}

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		panic(err.Error())
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		panic(err.Error())
	}

	labelSelector, err := labels.Parse("decMgmtRequires-*")
	if err != nil {
		panic(err)
	}

	// Services
	serviceWatchlist := cache.NewFilteredListWatchFromClient(
		clientset.CoreV1().RESTClient(),
		"services",
		metav1.NamespaceAll,
		func(options *metav1.ListOptions) {
			options.LabelSelector = labelSelector.String()
		},
	)

	_, serviceInformer := cache.NewInformer(
		serviceWatchlist,
		&corev1.Service{},
		30*time.Second,
		cache.ResourceEventHandlerFuncs{
			AddFunc: func(obj interface{}) {
				fmt.Println("Service added:", obj.(*corev1.Service).Name)
			},
			DeleteFunc: func(obj interface{}) {
				fmt.Println("Service deleted:", obj.(*corev1.Service).Name)
			},
			UpdateFunc: func(oldObj, newObj interface{}) {
				fmt.Println("Service updated:", newObj.(*corev1.Service).Name)
			},
		},
	)

	// Deployments
	deploymentWatchlist := cache.NewFilteredListWatchFromClient(
		clientset.AppsV1().RESTClient(),
		"deployments",
		metav1.NamespaceAll,
		func(options *metav1.ListOptions) {
			options.LabelSelector = labelSelector.String()
		},
	)

	_, deploymentInformer := cache.NewInformer(
		deploymentWatchlist,
		&appsv1.Deployment{},
		30*time.Second,
		cache.ResourceEventHandlerFuncs{
			AddFunc: func(obj interface{}) {
				fmt.Println("Deployment added:", obj.(*appsv1.Deployment).Name)
			},
			DeleteFunc: func(obj interface{}) {
				fmt.Println("Deployment deleted:", obj.(*appsv1.Deployment).Name)
			},
			UpdateFunc: func(oldObj, newObj interface{}) {
				fmt.Println("Deployment updated:", newObj.(*appsv1.Deployment).Name)
			},
		},
	)

	stop := make(chan struct{})
	go serviceInformer.Run(stop)
	go deploymentInformer.Run(stop)
	defer close(stop)

	select {}
}
