###
### this simulation is meant to determine the probability that a useful feature
### will not be chosen over a useless feature
###
### by James Long
### date Dec 3, 2010
###

library('rpart')


###
### it appears that CART almost always identifies the correct variable as being
### the most important
###


# set parameters for experiment
n = 151
n_high = 17
z = factor(c(rep("high",n_high),rep("low",n-n_high)))
uvot_detection = factor(c(rep("no",13),rep("yes",4),rep("no",36),rep("yes",98)))
control1 = rpart.control(maxdepth=3)
data1 = data.frame(z,uvot_detection,runif(n))
priors = 1:19 / 20
n_iter = 2000
results = rep(0,length(priors))
table(data1$z,data1$uvot_detection)

# get results
for(i in 1:n_iter){
  print(i)
  data1 = data.frame(z,uvot_detection,runif(n))
  for(j in 1:length(priors)){
    fit1 = rpart(z ~ .,data=data1,method='class',control=control1,parms=list(prior=c(priors[j],1-priors[j])))
    varsUsed = fit1$frame["1",1]
    if(varsUsed == "uvot_detection"){
      results[j] = results[j] + 1
    }
  }
}
results = results / n_iter

# output results
pdf('type_1_error_full.pdf')
plot(priors,results)
dev.off()






###
### now imitate CV setting, how hard is it to identify first split
###

# set experiment parameters
n = 121
n_high = 12
z = factor(c(rep("high",n_high),rep("low",n-n_high)))
uvot_detection = factor(c(rep("no",9),rep("yes",3),rep("no",29),rep("yes",80)))
control1 = rpart.control(maxdepth=3)
data1 = data.frame(z,uvot_detection,runif(n))
priors = 1:19 / 20
n_iter = 1000
results = rep(0,length(priors))
table(data1$z,data1$uvot_detection)

# get results
for(i in 1:n_iter){
  print(i)
  data1 = data.frame(z,uvot_detection,runif(n))
  for(j in 1:length(priors)){
    fit1 = rpart(z ~ .,data=data1,method='class',control=control1,parms=list(prior=c(priors[j],1-priors[j])))
    varsUsed = fit1$frame["1",1]
    if(varsUsed == "uvot_detection"){
      results[j] = results[j] + 1
    }
  }
}
results = results / n_iter




# print results
pdf('type_1_error_cv.pdf')
plot(priors,results)
dev.off()

