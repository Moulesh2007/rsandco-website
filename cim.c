#include<stdio.h>
#include<conio.h>
#include<stdlib.h>
#include<string.h>
struct table
{

7

char var[10]; int value;
};
struct table tbl[20]; int i,j,n;
void create(); void modify();
int search(char variable[],int n); void insert();
void display(); void main()
{
int ch,result=0; char v[10]; clrscr();
do
{
printf("Enter your choice\n1.Create\n2.Insert\n3.Modify\n4.Search\n5.Display\n6.Exit:");scanf("%d",&ch);
switch(ch)
{
case 1:
case 2:
case 3:
case 4:
create(); break;
insert(); break;
modify(); break;
printf("Enter the variable to be searched for:\n"); scanf("%s",&v);
result=search(v,n); if(result==0)
printf("The variable does not belong to the table\n"); else
printf("The location of the variable is %d\nThe value of %s is
%d\n",result,tbl[result].var,tbl[result].value); break;
}
while(ch!=6);
getch();
}
case 5:
case 6:
}
display(); break;
exit(1);
void create()
{
printf("Enter the no. of entries:"); scanf("%d",&n);
printf("Enter the variable and the value:\n"); for(i=1;i<=n;i++)
{
scanf("%s%d",tbl[i].var,&tbl[i].value); check: if(tbl[i].var[0]>='0'&&tbl[i].var[0]<='9')
{
}
check1:
printf("The variable should start with an alphabet\nEnter correct variable name:\n");

8

scanf("%s%d",tbl[i].var,&tbl[i].value);
goto check;
for(j=1;j<i;j++)
{
if(strcmp(tbl[i].var,tbl[j].var)==0)
{
printf("The variable already exists.Enter another variable\n"); scanf("%s%d",tbl[i].var,&tbl[i].value);
goto check1;
}
}
}
printf("The table after creation is:\n"); display();
}
void insert()
{
if(i>=20)
printf("Cannot insert.Table isfull\n");
else
{
n++;
printf("Enter the value and variable\n"); scanf("%s%d",tbl[n].var,&tbl[n].value); check:
if(tbl[i].var[0]>='0'&&tbl[i].var[0]<='9')
{
}
check1:
printf("The variable should start with an alphabet\nEnter correct variable name:\n");
scanf("%s%d",tbl[i].var,&tbl[i].value);
goto check;
for(j=1;j<n;j++)
{
if(strcmp(tbl[j].var,tbl[i].var)==0)
{
printf("The variable already exist.Enter another variable\n"); scanf("%s%d",tbl[i].var,&tbl[i].value);
goto check1;
}
}
printf("The table after insertion is:\n"); display();
}
}
void modify()
{
char variable[10]; int result=0;
printf("Enter the variable to be modified\n"); scanf("%s",&variable); result=search(variable,n);
if(result==0)

9

printf("%s does not belong to table\n",variable);
else
{
printf("The current value of the variable %s is %d\nEnter the new variable and its
value\n",tbl[result].var,tbl[result].value); scanf("%s%d",tbl[result].var,&tbl[result].value);
check: if(tbl[i].var[0]>='0'&&tbl[i].var[0]<='9')
{
printf("The variable should start with an alphabet\nEnter correct variable name:\n");
scanf("%s%d",tbl[i].var,&tbl[i].value);
goto check;
}
}
printf("The table after modification is:\n"); display();
}
int search(char variable[],int n)
{
int flag; for(i=1;i<=n;i++)
{
if(strcmp(tbl[i].var,variable)==0)
{
flag=1; break;
}
}
if(flag==1)
return i;
else
return 0;
}
void display()
{
printf("VARIABLE\t VALUE\n"); for(i=1;i<=n;i++)
printf("%s\t\t%d\n",tbl[i].var,tbl[i].value);