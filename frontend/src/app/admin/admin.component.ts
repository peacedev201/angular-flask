import { Component, OnInit, ChangeDetectorRef, OnDestroy } from '@angular/core';
import { MediaMatcher } from '@angular/cdk/layout';
import { AuthService } from '../services/auth.service';
import { AdminService } from 'src/app/services/admin.service';
import { AdminUser } from 'src/app/models/admin.model';

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.scss']
})
export class AdminComponent implements OnInit, OnDestroy {


  mobileQuery: MediaQueryList;
  notification
  check_notification=false

  sideBar = [
    { url: '/admin/dashboard', label: 'Dashboard', role: 'editor' },
    { url: '/admin/contributors', label: 'Contributors', role: 'editor' },
    { url: '/admin/items', label: 'Items', role: 'editor' },
    { url: '/admin/users', label: 'User Management', role: 'admin' },
    { url: '/admin/security', label: 'Security', role: 'editor' },
  ];


  private mobileQueryListener: () => void;

  constructor(changeDetectorRef: ChangeDetectorRef, media: MediaMatcher, private authService: AuthService, private admin: AdminService) {
    this.mobileQuery = media.matchMedia('(max-width: 1024px)');
    this.mobileQueryListener = () => changeDetectorRef.detectChanges();
    this.mobileQuery.addEventListener('change', this.mobileQueryListener);
  }

  ngOnInit() { 
    if(this.authService.currentUserValue.role == "admin"){
      this.admin.loadUserList().subscribe((res: AdminUser[]) => {
        // console.log(res)
        let i = 0
        res.forEach(element => {
          if(element.role == 'notallowed'){
            i = i + 1;
          }
        });
        this.notification = i
        this.check_notification = true;
        if(i==0){
          this.check_notification = false;
        }
      }, (err) => {
      });
      if(localStorage.getItem("currentUser")){
        this.notification = localStorage.getItem("notification");
        if(this.notification !=""){
          this.check_notification = true;
        }
      }
    }
  }

  ngOnDestroy() {
    this.mobileQuery.removeEventListener('change', this.mobileQueryListener);
  }

  getCheckUserRole(side) {
      switch (this.authService.currentUserValue.role) {
        case 'admin':
          return true;
        case 'editor':
          switch (side.role) {
            case 'editor':
              return true;
            default:
              return false;
          }
        default:
          return false;
      }    
  }
}
