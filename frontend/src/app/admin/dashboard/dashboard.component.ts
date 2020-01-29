import { Component, OnInit } from '@angular/core';
import { NotificationService } from 'src/app/services/notification.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {

  constructor(private notify: NotificationService) { }

  ngOnInit() {
  }

  testButtonClick() {
    this.notify.sendMessage('this is test');
  }

}
