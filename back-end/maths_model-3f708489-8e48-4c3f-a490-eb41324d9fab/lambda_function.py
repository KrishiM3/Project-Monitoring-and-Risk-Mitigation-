import boto3
import numpy as np
from scipy.optimize import minimize
import json
from datetime import datetime

from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer

from uuid import uuid4


#Defining contraints
#Equality constraint requires constraint function to return 0 to pass
#Inequality contraint requires contraint function to return a non-negative value to pass

#k*teamskill*teamsize*communnications >= a*Cumulative lateness+ b*scope creep + c*bugs
def constraint1(metricArr, cofArr, flip):
    lateness=metricArr[7]
    scopeCreep=metricArr[4]
    bugs=metricArr[6]
    teamSkill=metricArr[3]
    teamsize=metricArr[1]
    communnications=metricArr[5]
    k=cofArr[0]
    A=cofArr[1]
    B=cofArr[2]
    C=cofArr[3]
    
    LHS=k*teamSkill*teamsize*communnications
    RHS=A*lateness + B*scopeCreep + C*bugs
    return LHS-RHS

#Project progression >= weeks so far / total weeks
def constraint2(metricArr, flip):
    totalWeeks=metricArr[10]
    weeksLeft=metricArr[9]
    progress=metricArr[2]

    weeksSpent=totalWeeks=weeksLeft
    LHS=progress
    RHS=weeksSpent/totalWeeks
    return LHS-RHS

#Project progression >= money spent so far / budget
def constraint3(metricArr, flip):
    budget=metricArr[0]
    moneySpent=metricArr[11]
    progress=metricArr[2]

    LHS=progress
    RHS=moneySpent/budget
    return LHS-RHS

#Salary / team size >= teamskill * k
def constraint4(metricArr, k, flip):
    salary=metricArr[12]
    teamSize=metricArr[1]
    teamSkill=metricArr[3]

    LHS=salary/teamSize
    RHS=teamSkill*k
    return LHS-RHS

#k*teamsize*teamskill * timeleft/(total time) >= UnresolvedBugs  KRISHI CHANGED THIS
def constraint5(metricArr, k, flip):
    bugs=metricArr[6]
    totalWeeks=metricArr[10]
    weeksLeft=metricArr[9]
    teamSize=metricArr[1]
    teamSkill=metricArr[3]

    LHS=k*teamSize*teamSkill*((totalWeeks - weeksLeft)/totalWeeks)
    RHS=bugs
    return LHS-RHS

#Team skill*communication >= parties Involved*k
def constraint6(metricArr, k, flip):
    communication=metricArr[5]
    partiesInvolved=metricArr[8]
    teamSkill=metricArr[3]

    LHS=teamSkill*communication
    RHS=k*partiesInvolved
    return LHS-RHS

#communication*Team skill / team size>= k*partiesInvlovled
def constraint7(metricArr, k, flip):
    communication=metricArr[5]
    teamSize=metricArr[1]
    teamSkill=metricArr[3]
    partiesInvolved=metricArr[8]

    LHS=(teamSize*teamSkill)/communication
    RHS=k*partiesInvolved
    return LHS-RHS

#Budget/ amount of weeks for deadline >= money spent / weeks passed so far
def constraint8(metricArr, flip):
    totalWeeks=metricArr[10]
    weeksLeft=metricArr[9]
    budget=metricArr[0]
    moneySpent=metricArr[11]
    
    weeksSpent=totalWeeks=weeksLeft
    LHS=budget / totalWeeks
    RHS=moneySpent/weeksSpent
    return LHS-RHS

#(Budget - expenditure) * timeleft/(total time) >= scope creep * k 
def constraint9(metricArr, k, flip):
    totalWeeks=metricArr[10]
    weeksLeft=metricArr[9]
    budget=metricArr[0]
    moneySpent=metricArr[11]
    scopeCreep=metricArr[4]
    
    LHS= (budget - moneySpent) * (weeksLeft/totalWeeks)
    RHS=scopeCreep*k
    return LHS-RHS

#((Budget - expenditure)/(totals weeks left + (lateness/7)) >= expenditure/ total weeks passed
def constraint10(metricArr, flip):
    totalWeeks=metricArr[10]
    weeksLeft=metricArr[9]
    budget=metricArr[0]
    moneySpent=metricArr[11]
    lateness=metricArr[7]  
    
    LHS= (budget - moneySpent) * (weeksLeft + (lateness/7))
    RHS=moneySpent/totalWeeks
    return LHS-RHS

#Project progression  * team skill >= k * lateness * time left/ (total time)
def constraint11(metricArr, k, flip):
    totalWeeks=metricArr[10]
    weeksLeft=metricArr[9]
    teamSkill=metricArr[0]
    progress=metricArr[3]
    lateness=metricArr[2]
    
    LHS= progress*teamSkill
    RHS=k * lateness * weeksLeft / totalWeeks
    return LHS-RHS

def calculateRisk(userMetrics, coefficients, flip):

    #This is calculating the distance between closestPoint and userInput
    def objective_function(closestPoint):
        diffArr = closestPoint - userMetrics
        distance = np.linalg.norm(diffArr)
        return distance
    
    const1Coeff=[coefficients[0], coefficients[1], coefficients[2], coefficients[3]]
    allCons = [{'type':'ineq', 'fun':constraint1, 'args':[const1Coeff, flip]},
               {'type':'ineq', 'fun':constraint2, 'args':[flip]},
               {'type':'ineq', 'fun':constraint3, 'args':[flip]},
               {'type':'ineq', 'fun':constraint4, 'args':[coefficients[4], flip]},
               {'type':'ineq', 'fun':constraint5, 'args':[coefficients[5], flip]},
               {'type':'ineq', 'fun':constraint6, 'args':[coefficients[6], flip]},
               {'type':'ineq', 'fun':constraint7, 'args':[coefficients[7], flip]},
               {'type':'ineq', 'fun':constraint8, 'args':[flip]},
               {'type':'ineq', 'fun':constraint9, 'args':[coefficients[8], flip]},
               {'type':'ineq', 'fun':constraint10, 'args':[flip]},
               {'type':'ineq', 'fun':constraint11, 'args':[coefficients[9], flip]}]
    
    # Find the closest point in the feasible region to the arbitrary point
    #Set initialGuess to some project that we know is in feasaible region
    brev = {"maxiter" : 2000000000}
    highest = float('inf') 
    initialGuess = np.array([1000000,10,0.7,10,0,10,0,0,1,50,100,500000,4000])
    secondGuess  = np.array([1000,10,0.7,10,0,10,0,0,1,50,100,400,4000])
    thirdGuess   = np.array([13000,10,0.5,9,0,9,0,0,3,50,100,6000,4500])
    fourthGuess = np.array([13000,100,0.5,100,0,100,0,0,3,50,100,6000,4500])
    result = minimize(objective_function, initialGuess, method='SLSQP', constraints=allCons, options=brev)
    if result['fun'] < highest:
        highest = result['fun']
    result = minimize(objective_function, secondGuess, method='SLSQP', constraints=allCons, options=brev)
    if result['fun'] < highest:
        highest = result['fun']
    result = minimize(objective_function, thirdGuess, method='SLSQP', constraints=allCons, options=brev)
    if result['fun'] < highest:
        highest = result['fun']  
    result = minimize(objective_function, fourthGuess, method='SLSQP', constraints=allCons, options=brev)
    if result['fun'] < highest:
        highest = result['fun']    
    distance=highest
    print("Distance from feasible region is "+str(distance))
    print(result)
    return distance




def learnBetterCoefficients(metrics, coefficients, success):
    print("--------------Whilst learning distances will be output a lot you can ignore this--------------")
    
    oldDist=calculateRisk(metrics, coefficients, 1)
    
    #In either of these cases the model does not need to change
    if (success==True and oldDist==0) or (success==False and oldDist>0):
        return
    
    #If a projcet failed but is inside the feasible reigion we need to flip the inequalities
    if oldDist==0 and success==False:
        flip=-1
    else:
        flip=1
     
    #Looping through every coefficient and checking if increasing or decreasing it 
    #by some small value moves the feasible region closer to the project
    for index in range(len(coefficients)):
        oldCof=coefficients[index]
        #random() generates a random value between 1 and 0
        shiftVal=10*np.random.random_sample(1)[0]
        multiplier=(100+shiftVal)/100
        coefficients[index]=oldCof*multiplier
        increasedCofDist=calculateRisk(metrics, coefficients, flip)
        if increasedCofDist>oldDist:
            multiplier=(100-shiftVal)/100
            coefficients[index]=oldCof*multiplier
            decreasedCofDist=calculateRisk(metrics, coefficients, flip)
            if decreasedCofDist>oldDist:
                coefficients[index]=oldCof
    print("--------------Stop ignoring now--------------")
    print("New coefficients are:")
    print(coefficients)
    print(insert_coeffiecient(coefficients))
                    


#This function calculates the distance from a project defined as metricArr and each constraint
#We can then look at the constraint with the largest distance and recommend a change to the user
#Each constraint is defined such that we want the RHS of the inequality to be greater than the LHS
#of the inequality so the suggestion would be to increase the metrics on the RHS or decrease the
#metrics of the LHS of the inequality causing the greatest distance
#A negative distance value means that the project is 'passing' that constraint
def recommendChange(metricArr, coefficients):
    
    #This hashmap will map a constraint number + increase or decrease key to
    #of the metrics involved with that constraint that should be increased or
    #decreased respectivley
    metricSuggestions={1: "increase the teamskill teamsize and quality of communications in the team and meet deadlines quicker reduce scope creep and reduce the number of bugs", 
                      2: "Inrease project_progression as you are behind scedule",
                      3: "Decrease the amount of money you are spending per week as you are on track to run out before you complete the project",
                      4: "Increase you salary as your employees are being underpaid and therefore wont be as productive",
                      5: "Increase your teamsize and teamskill as you currently will not be able to fix all the bugs in the project before the deadline",
                      6: "Increase your teamskill and communication as they are not high enough relative to the number of parties involved in the project",
                      7: "Decrease teamsize or increase communication and teamskill as the current team is not skilled enough to work across such a big team and is not communicating enough",
                      8: "Decrease the amount of money you are spending per week as you are currenlty on track to run out of money before the deadline",
                      9: "Increase you rbudget as you currently cannot afford to complete all the extra tasks that were added after the initial requirments",
                      10: "Decrease lateness and money spent per week or increase the budget as you will run out of money before the projected is finished as a result of missing too many deadlines",
                      11: ["Increase teamskill and project progression as the current team has fallen to far behind to finish the project before the deadline"]                   
                      }
 
    const1Coeff=[coefficients[0], coefficients[1], coefficients[2], coefficients[3]]
    
    distances=list(range(11))
    distances[0] = -1 * constraint1(metricArr, const1Coeff, 1)
    distances[1] = -1 * constraint2(metricArr, 1)
    distances[2] = -1 * constraint3(metricArr, 1)
    distances[3] = -1 * constraint4(metricArr, coefficients[4], 1)
    distances[4] = -1 * constraint5(metricArr, coefficients[5], 1)
    distances[5] = -1 * constraint6(metricArr, coefficients[6], 1)
    distances[6] = -1 * constraint7(metricArr, coefficients[7], 1)
    distances[7] = -1 * constraint8(metricArr, 1)
    distances[8] = -1 * constraint9(metricArr, coefficients[8], 1)
    distances[9] = -1 * constraint10(metricArr, 1)
    distances[10] = -1 * constraint11(metricArr, coefficients[9], 1)
    
    maxDist=0
    mostCostlyConstraint= None
    for index in range(len(distances)):
        if distances[index]>maxDist:
            maxDist=distances[index]
            mostCostlyConstraint=index+1

    print("The cost of each constraint is: ")
    print(distances)
    print("The constraint causing the most risk is "+str(mostCostlyConstraint))
    if mostCostlyConstraint is not None:
        recomendedChange=metricSuggestions[mostCostlyConstraint]
    else:
        recomendedChange="No changes are required"
    print(recomendedChange)
    
    return recomendedChange


##This function is to determine the riskiness based on constraint 2 , as the worst case distance will be 1 for 
## this constraint it will be beneficial if we properly determined riskiness using this constraint.
def determinePP(metricArr):
    if metricArr[2] - (metricArr[9]/metricArr[10]) > 0:
        return 1 
    elif metricArr[2] - (metricArr[9]/metricArr[10]) > -0.1:
        return 2 
    elif metricArr[2] - (metricArr[9]/metricArr[10]) > -0.2:
        return 3 
    elif metricArr[2] - (metricArr[9]/metricArr[10]) > -0.35:
        return 4
    else:
        return 5


def determinePs(metricArr):
    if metricArr[2] - (metricArr[11]/metricArr[0]) > 0:
        return 1
    elif metricArr[2] - (metricArr[11]/metricArr[0]) > -0.15:
        return 2
    elif metricArr[2] - (metricArr[11]/metricArr[0]) > -0.3:
        return 3
    elif metricArr[2] - (metricArr[11]/metricArr[0]) > -0.45:
        return 4 
    else: 
        return 5

def determineRisk(distance, param1, param2):
    riskLevels = ["Not risky", "slightly risk", "Risky", "Very Risky", "Extremely Risky"]
    if distance < 5:
        riskIndex =  max(1,param1,param2)
    elif distance < 10:
        riskIndex = max(2,param1,param2)
    elif distance < 20:
        riskIndex = max(3,param1,param2)
    elif distance < 40: 
        riskIndex = max(4,param1,param2)
    else:
        riskIndex = 5
    #return riskLevels[riskIndex-1]
    return float(riskIndex)


def lambda_handler(event, context):
    try:
        event = json.loads(event['body'])
        project_id = event.get('project_id')
        print(project_id)
        dynamodb = boto3.client('dynamodb')
        
        response = dynamodb.get_item(
            TableName = 'Project_Metrics',
            Key={'project_id': {'S':project_id}}
        )
        
        coefficientData = dynamodb.get_item(
            TableName = 'coefficient_table',
            Key={'id': {'N': '0'} }
        )
        coefficientArray=coefficientData['Item']['coefficient_values']['L']
        print("Coefficient array is")
        coefficientArray = [float(x['N']) for x in coefficientArray]
        print(coefficientArray)
    
        
        #Getting the metrics for this project from the database
        budget              = response['Item']['budget']['N']
        team_size           = response['Item']['team_size']['N']
        project_progression = response['Item']['project_progression']['N']
        team_skill          = response['Item']['team_skill']['N']
        scope_creep         = response['Item']['scope_creep']['N']
        communication       = response['Item']['communication']['N']
        git_bugs            = response['Item']['git_bugs']['N']
        lateness            = response['Item']['lateness']['N']
        parties_involved    = response['Item']['parties_involved']['N']
        days_passed         = response['Item']['days_passed']['N']
        total_days          = response['Item']['total_days']['N']
        money_spent         = response['Item']['money_spent']['N']
        salary              = response['Item']['salary']['N']
        
        metrics=np.array([budget, team_size, project_progression, team_skill, scope_creep, communication, git_bugs
        ,lateness, parties_involved, days_passed, total_days, money_spent, salary]).astype(float)
        
        
        #Deciding if this model is completed or not and therefore if we want to learn
        #from it or calculate the risk of it
        learn = event.get('learn')
        if learn == "False":
            riskDistance=calculateRisk(metrics, coefficientArray, 1)
            PP = determinePP(metrics)
            Ps = determinePs(metrics)
            risk = determineRisk(riskDistance, PP, Ps)
            #print(risk)
            # risk=riskDistance
            update_risk(project_id, risk)
            rc = recommendChange(metrics, coefficientArray)
            dynamodb.put_item(
                TableName='Evaluations',
                Item={
                    'id': {'S': uuid4() },
                    'risk': {'N': str(risk)},
                    'project_id': {'S': project_id },
                    'timestamp': {'S': str(datetime.now())}
                }
            )
        else:
            #Finding out if the project failed or succeeded
            projectInfo = dynamodb.get_item(
            TableName = 'Project',
            Key={'project_id': {'S':project_id}}
            )
            success = projectInfo['Item']['status']['N']
            learnBetterCoefficients(metrics, coefficientArray, success)
            
        item = response["Item"]
        deserializer = boto3.dynamodb.types.TypeDeserializer()
        item = {k: deserializer.deserialize(v) for k,v in item.items()}
            
        return { 
            'statusCode': 200,
            'body': {
                'item': item,
                'risk': risk,
                'change': rc,
                'pp': PP
            }
        };
    except Exception as e:
        return { 
            'statusCode': 400,
            'err': json.dumps(str(e)) 
        };


"-----------"
#The function will be called in 'learn' function to insert the learned coefficient into coefficient table.
def insert_coeffiecient(coefficient_inserted):
    dynamodb = boto3.client('dynamodb')
    table_name = 'coefficient_table'
    coefficient_value = coefficient_inserted
    coefficient_list = [{'N': str(coeff)} for coeff in coefficient_value]
    
    #test_coefficients = [{'N':str(0.01)},{'N':str(5)},{'N':str(5)},{'N':str(5)},{'N':str(1)},{'N':str(1)},{'N':str(15)},{'N':str(35.7142857143)},{'N':str(1)},{'N':str(1)}]
    
    try:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'id':{'N':'0'},
                'coefficient_values': {'L': test_coefficients}
            }
        )
    except Exception as e:
        return {"code": 500, "message": f"An unexpected error occurred while adding coefficient: {e}"}
    else:
        return {"code": 200, "message": "Coefficient added successfully"}
"----------------------------------------------------------------------------------------------------------"
def update_risk(projectID, riskLevel):
    print("This is inside the updateRisk")
    print(projectID)
    # create a DynamoDB client
    dynamodb = boto3.client('dynamodb')
    
    # specify the table name and the key to update
    table_name = 'Project'
    key = {'project_id': {'S': projectID}}
    
    # specify the update expression and the attribute values
    update_expression = 'SET #attr = :val'
    expression_attribute_names = {'#attr': 'risk_eval'}
    expression_attribute_values = {':val': {'S': str(riskLevel)}}
    
    # call the update_item method to update the item
    dynamodb.update_item(
        TableName=table_name,
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values
    )
    
    try:
        # call the update_item method to update the item
        dynamodb.update_item(
            TableName=table_name,
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
    except Exception as e:
        return {"code": 500, "message": f"An unexpected error occurred while adding coefficient: {e}"}
    else:
        return {"code": 200, "message": "Coefficient added successfully"}
"----------------------------------------------------------------------------------------------------------"


'''
#Define a metric dictionary to use as input to model
[0]=Budget
[1]=Team Size
[2]=Project Progression
[3]=Team Skill
[4]=Scope Creep
[5]=communication
[6]=Git Bugs
[7]=Deadlines (Cumulative Lateness)
[8]=Parties involved
[9]=Days Passed
[10]=Total days initially given to complete project
[11]=moneySpent
[12]=Salary
'''

'''
#Define a coefficient dictionary to use as input to model
[0]=k for constraint1
[1]=a for constraint1
[2]=b for constraint1
[3]=c for constraint1
[4]=k for constraint4
[5]=k for constraint5
[6]=k for constraint6
[7]=k for constraint7
[8]=k for constraint9
[9]=k for constraint11
'''
