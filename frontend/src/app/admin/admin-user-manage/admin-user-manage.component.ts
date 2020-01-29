import { Component, OnInit , Output, EventEmitter} from '@angular/core';
import { AdminService } from 'src/app/services/admin.service';
import { AdminUser } from 'src/app/models/admin.model';

declare var $: any;

interface Alert {
  type: string;
  message: string;
}

@Component({
  selector: 'app-admin-user-manage',
  templateUrl: './admin-user-manage.component.html',
  styleUrls: ['./admin-user-manage.component.scss']
})
export class AdminUserManageComponent implements OnInit {

  public userlist: AdminUser[];
  public msgAlert = {
    type: '',
    message: '',
  };

  public USER_ROLE = [
    { label: 'Admin', value: 'admin' },
    { label: 'Editor', value: 'editor' },
    { label: 'Not Allowed', value: 'notallowed' },
  ];

  @Output() someEvent = new EventEmitter<string>();

  constructor(private admin: AdminService) { }

  ngOnInit() {
    this.loadUserList();
  }

  private loadUserList() {
    this.admin.loadUserList().subscribe((res: AdminUser[]) => {
      this.userlist = res;
      // console.log(res)
      let i = 0
      res.forEach(element => {
        if(element.role == 'notallowed'){
          i = i + 1;
        }
      });
      if(i != 0){
        localStorage.setItem("notification", i.toString());
      }
      $(document).ready(function() {
        console.log($(".notification"), i)
        if(i == 0){
          $(".notification").text('');
        }
        else{
          $(".notification").text(i);
        }
      });
    }, (err) => {
      this.msgAlert.type = 'danger';
      this.msgAlert.message = err;
    });
  }

  public updateUserInformation(user: AdminUser) {
    this.admin.updateAdminUser(user).subscribe((res) => {
      this.msgAlert.type = 'info';
      this.msgAlert.message = 'Success';
      this.loadUserList();
    }, err => {
      this.msgAlert.type = 'danger';
      this.msgAlert.message = err;
    });

  }

  public deleteUserInformation(user: AdminUser) {
    this.admin.deleteAdminUser(user).subscribe((res) => {
      this.msgAlert.type = 'info';
      this.msgAlert.message = 'Success';
      this.loadUserList();
    }, err => {
      this.msgAlert.type = 'danger';
      this.msgAlert.message = err;
    });
  }
  closeAlert(alert: Alert) {
    this.msgAlert.message = '';
  }
}
