import { Component, OnInit } from '@angular/core';
import { AdminService } from 'src/app/services/admin.service';
import { PersonDetailModel } from 'src/app/models/personal.model';
import { OrganizationModel } from 'src/app/models/admin.model';
import { SurveyService } from 'src/app/services/survey.service';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from 'src/app/services/auth.service';

@Component({
  selector: 'app-user-approve-list',
  templateUrl: './user-approve-list.component.html',
})
export class UserApproveListComponent implements OnInit {

  public orgPersons: PersonDetailModel[] = [];
  public orgsList: OrganizationModel[] = [];

  constructor(public adminService: AdminService, public survey: SurveyService, public authService: AuthService) { }

  ngOnInit() {
    this.loadUserList();
    this.loadOrgList();

  }

  loadUserList() {
    this.adminService.getUsersList().subscribe((res: PersonDetailModel[]) => {
      console.log(res);
      this.orgPersons = res;
    });
  }

  loadOrgList() {
    this.adminService.getOrganizationList().subscribe((res: OrganizationModel[]) => {
      this.orgsList = res;
    });
  }
}
