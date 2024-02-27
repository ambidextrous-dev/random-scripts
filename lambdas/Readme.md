## Lambdas

I created these lambdas because for a scenario, I wanted to keep the isntances created by an ASG out of the same pool of private IP's. 

When a new instance is spun up/terminated, the ASG fires a lifecycle hook. The lifecyle hook is caught by Eventbridge which then further invokes the lambdas. The lambdas then attach/detach the ENI's. In my case, I further updated the startup lambda in a way that I do not need to use shutdown lambda any more. 

The startup lambda goes through the list of ENI's in the parameter store, till it finds one which is available.


Inspired by: https://someshsrivastava1983.medium.com/how-to-get-the-same-private-static-ip-always-attached-to-an-ec2-instance-in-auto-scaling-group-c4bc26d14b49
