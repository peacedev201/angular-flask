import { Component, OnInit } from '@angular/core';
import { AdminService } from 'src/app/services/admin.service';
import { SurveyService } from 'src/app/services/survey.service';
import { PersonDetailModel } from 'src/app/models/personal.model';
import { OrganizationModel } from 'src/app/models/admin.model';
import { ActivatedRoute, Router } from '@angular/router';
import { MatDialog } from '@angular/material';
import { ConfirmDlgComponent } from 'src/app/components/shared/dialog/confirm-dlg/confirm-dlg.component';

@Component({
  selector: 'app-user-change-history',
  templateUrl: './user-change-history.component.html',
  styles: [`
  th, td{
    vertical-align: middle !important;
  }
  `]
})
export class UserChangeHistoryComponent implements OnInit {
  public orgPersons: PersonDetailModel[] = [];
  public orgsList: OrganizationModel[] = [];
  public userId = '';
  constructor(private adminService: AdminService, public survey: SurveyService, private route: ActivatedRoute, private router: Router,
    public dialog: MatDialog) { }
  readonly redirectURL = '/admin/contributors';

  ngOnInit() {
    this.userId = this.route.snapshot.params['user-id'];
    if (!this.userId) {
      this.router.navigate([this.redirectURL]);
    }
    this.loadUserList();
    this.loadOrgList();
    console.log('--------this.userId------');
    console.log(this.userId);
  }

  loadUserList() {
    this.adminService.getUsersList().subscribe((res: PersonDetailModel[]) => {

      this.orgPersons = res.filter((person) => {
        return +person.userid === +this.userId;
      });
      console.log(this.orgPersons);
    });
  }

  loadOrgList() {
    this.adminService.getOrganizationList().subscribe((res: OrganizationModel[]) => {
      this.orgsList = res;
    });
  }

  clickApprove(postid) {
    const person = this.orgPersons.find((curP) => curP.postid === postid);
    this.adminService.updateUser({
      ...person,
      organizations: person.organizations.map((orgName) => this.orgsList.find(org => org.name === orgName).id)
    }).subscribe(res => {
      console.log(res);
      this.router.navigate([this.redirectURL]);
    });
  }
  openDialog(title, content, type, color) {
    const dialogRef = this.dialog.open(ConfirmDlgComponent, {
      width: '250px',
      data: {
        title, content, type, color
      }
    });

    return dialogRef.afterClosed();
  }

  clickDeclined(postid) {
    this.openDialog('Decline Confirm', 'Do you want to decline this changes?', 'confirm', 'danger').subscribe(result => {
      if (result === 'true') {
        const person = this.orgPersons.find((curP) => curP.postid === postid);
        this.adminService.deleteUser(person.postid).subscribe(res => {
          console.log(res);
          this.router.navigate([this.redirectURL]);
        });
      }
    });
  }

}
